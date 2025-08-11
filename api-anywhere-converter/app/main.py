# Standard library imports
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

# Third-party imports
import pandas as pd
import sqlalchemy as sa
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, Text
from sqlalchemy.ext.declarative import declarative_base
import strawberry
from strawberry.fastapi import GraphQLRouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="API Anywhere Converter",
    description="Auto-generate REST and GraphQL APIs from databases and CSV files",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("CORS_ORIGIN") == "*" else os.getenv("CORS_ORIGIN", "").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
db_engines = {}
csv_tables = {}
csv_next_ids = defaultdict(int)  # Track next ID for CSV records
default_db_url = os.getenv("DB_URL")  # Get default DB URL from environment

# Pydantic models
class DatabaseConnection(BaseModel):
    db_url: str
    table_name: Optional[str] = None

class CSVUpload(BaseModel):
    filename: str
    table_name: str
    data: List[Dict[str, Any]]

class RecordData(BaseModel):
    data: Dict[str, Any]

def get_db_engine(db_url: str):
    """Get or create database engine"""
    if db_url not in db_engines:
        try:
            engine = create_engine(db_url)
            db_engines[db_url] = engine
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid database URL: {str(e)}")
    
    return db_engines[db_url]

def get_table_schema(engine, table_name: str):
    """Get table schema from database"""
    metadata = MetaData()
    try:
        table = Table(table_name, metadata, autoload_with=engine)
        return table
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table {table_name} not found: {str(e)}")

def create_csv_table(table_name: str, data: List[Dict[str, Any]]):
    """Create a virtual table from CSV data"""
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")
    
    # Add ID column to each record if not present
    for i, record in enumerate(data):
        if 'id' not in record:
            record['id'] = i + 1
    
    # Store CSV data in memory
    csv_tables[table_name] = {
        "data": data,
        "columns": list(data[0].keys()) if data else [],
        "row_count": len(data)
    }
    
    # Set next ID for this table
    csv_next_ids[table_name] = len(data) + 1
    
    return table_name

def get_csv_record_by_id(table_name: str, record_id: int):
    """Get a specific CSV record by ID"""
    if table_name not in csv_tables:
        raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
    
    for record in csv_tables[table_name]["data"]:
        if record.get('id') == record_id:
            return record
    
    raise HTTPException(status_code=404, detail=f"Record with ID {record_id} not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "API Anywhere Converter",
        "version": "1.0.0",
        "default_db_url": default_db_url is not None,
        "endpoints": {
            "health": "/health",
            "connect_db": "/connect",
            "upload_csv": "/upload",
            "tables": "/tables",
            "graphql": "/graphql",
            "docs": "/docs"
        }
    }

@app.post("/connect")
async def connect_database(connection: DatabaseConnection):
    """Connect to a database and generate APIs"""
    try:
        engine = get_db_engine(connection.db_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(sa.text("SELECT 1"))
            result.fetchone()
        
        # Get all tables if no specific table provided
        if connection.table_name:
            tables = [connection.table_name]
        else:
            metadata = MetaData()
            metadata.reflect(bind=engine)
            tables = list(metadata.tables.keys())
        
        # Get detailed schema information
        table_schemas = []
        for table_name in tables:
            try:
                table = get_table_schema(engine, table_name)
                columns = [{"name": col.name, "type": str(col.type)} for col in table.columns]
                table_schemas.append({
                    "name": table_name,
                    "columns": columns,
                    "source": "database"
                })
            except Exception as e:
                logger.warning(f"Could not get schema for table {table_name}: {e}")
        
        return {
            "status": "connected",
            "tables": tables,
            "schemas": table_schemas,
            "message": f"Successfully connected to database with {len(tables)} tables"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")

@app.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    table_name: str = Form(...)
):
    """Upload CSV file and create virtual table"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read CSV file
        df = pd.read_csv(file.file)
        data = df.to_dict('records')
        
        # Create virtual table
        table = create_csv_table(table_name, data)
        
        return {
            "status": "success",
            "table_name": table_name,
            "rows": len(data),
            "columns": list(data[0].keys()) if data else [],
            "message": f"CSV uploaded and table '{table_name}' created successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

@app.get("/tables")
async def list_tables(db_url: str = None):
    """List all tables in the database and CSV tables"""
    tables = []
    
    # Add CSV tables
    for table_name, table_info in csv_tables.items():
        tables.append({
            "name": table_name,
            "columns": table_info["columns"],
            "row_count": table_info["row_count"],
            "source": "csv"
        })
    
    # Use provided db_url or default from environment
    effective_db_url = db_url or default_db_url
    
    # Add database tables if URL provided
    if effective_db_url:
        try:
            engine = get_db_engine(effective_db_url)
            metadata = MetaData()
            metadata.reflect(bind=engine)
            
            for table_name, table in metadata.tables.items():
                columns = [{"name": col.name, "type": str(col.type)} for col in table.columns]
                tables.append({
                    "name": table_name,
                    "columns": columns,
                    "source": "database"
                })
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to list database tables: {str(e)}")
    
    return {"tables": tables}

@app.get("/api/{table_name}")
async def get_table_data(
    table_name: str,
    db_url: str = None,
    limit: int = 100,
    offset: int = 0
):
    """Get data from a table or CSV"""
    try:
        # Check if it's a CSV table first
        if table_name in csv_tables:
            csv_data = csv_tables[table_name]["data"]
            total_rows = len(csv_data)
            rows = csv_data[offset:offset + limit]
            
            return {
                "table": table_name,
                "data": rows,
                "total": total_rows,
                "limit": limit,
                "offset": offset,
                "source": "csv"
            }
        
        # Otherwise, try database table
        effective_db_url = db_url or default_db_url
        if not effective_db_url:
            raise HTTPException(status_code=400, detail="Database URL required for database tables")
            
        engine = get_db_engine(effective_db_url)
        table = get_table_schema(engine, table_name)
        
        with engine.connect() as conn:
            query = sa.select(table).limit(limit).offset(offset)
            result = conn.execute(query)
            rows = [dict(row._mapping) for row in result]
        
        return {
            "table": table_name,
            "data": rows,
            "total": len(rows),
            "limit": limit,
            "offset": offset,
            "source": "database"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get data: {str(e)}")

@app.get("/api/{table_name}/{record_id}")
async def get_record(
    table_name: str,
    record_id: int,
    db_url: str = None
):
    """Get a specific record by ID from CSV or database"""
    try:
        # Check if it's a CSV table first
        if table_name in csv_tables:
            record = get_csv_record_by_id(table_name, record_id)
            return {"record": record, "source": "csv"}
        
        # Otherwise, try database table
        effective_db_url = db_url or default_db_url
        if not effective_db_url:
            raise HTTPException(status_code=400, detail="Database URL required for database tables")
            
        engine = get_db_engine(effective_db_url)
        table = get_table_schema(engine, table_name)
        
        with engine.connect() as conn:
            query = sa.select(table).where(table.c.id == record_id)
            result = conn.execute(query)
            row = result.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Record not found")
            
            return {"record": dict(row._mapping), "source": "database"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get record: {str(e)}")

@app.post("/api/{table_name}")
async def create_record(
    table_name: str,
    record_data: RecordData,
    db_url: str = None
):
    """Create a new record in CSV or database"""
    try:
        # Check if it's a CSV table first
        if table_name in csv_tables:
            new_record = record_data.data.copy()
            new_record['id'] = csv_next_ids[table_name]
            csv_tables[table_name]["data"].append(new_record)
            csv_tables[table_name]["row_count"] += 1
            csv_next_ids[table_name] += 1
            
            return {
                "status": "created",
                "id": new_record['id'],
                "message": "Record created successfully",
                "source": "csv"
            }
        
        # Otherwise, try database table
        effective_db_url = db_url or default_db_url
        if not effective_db_url:
            raise HTTPException(status_code=400, detail="Database URL required for database tables")
            
        engine = get_db_engine(effective_db_url)
        table = get_table_schema(engine, table_name)
        
        with engine.connect() as conn:
            query = table.insert().values(**record_data.data)
            result = conn.execute(query)
            conn.commit()
            
            return {
                "status": "created",
                "id": result.inserted_primary_key[0] if result.inserted_primary_key else None,
                "message": "Record created successfully",
                "source": "database"
            }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create record: {str(e)}")

@app.put("/api/{table_name}/{record_id}")
async def update_record(
    table_name: str,
    record_id: int,
    record_data: RecordData,
    db_url: str = None
):
    """Update a record in CSV or database"""
    try:
        # Check if it's a CSV table first
        if table_name in csv_tables:
            for i, record in enumerate(csv_tables[table_name]["data"]):
                if record.get('id') == record_id:
                    # Preserve the ID
                    updated_record = record_data.data.copy()
                    updated_record['id'] = record_id
                    csv_tables[table_name]["data"][i] = updated_record
                    
                    return {
                        "status": "updated",
                        "message": "Record updated successfully",
                        "source": "csv"
                    }
            
            raise HTTPException(status_code=404, detail="Record not found")
        
        # Otherwise, try database table
        effective_db_url = db_url or default_db_url
        if not effective_db_url:
            raise HTTPException(status_code=400, detail="Database URL required for database tables")
            
        engine = get_db_engine(effective_db_url)
        table = get_table_schema(engine, table_name)
        
        with engine.connect() as conn:
            query = table.update().where(table.c.id == record_id).values(**record_data.data)
            result = conn.execute(query)
            conn.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Record not found")
            
            return {
                "status": "updated",
                "message": "Record updated successfully",
                "source": "database"
            }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update record: {str(e)}")

@app.delete("/api/{table_name}/{record_id}")
async def delete_record(
    table_name: str,
    record_id: int,
    db_url: str = None
):
    """Delete a record from CSV or database"""
    try:
        # Check if it's a CSV table first
        if table_name in csv_tables:
            for i, record in enumerate(csv_tables[table_name]["data"]):
                if record.get('id') == record_id:
                    del csv_tables[table_name]["data"][i]
                    csv_tables[table_name]["row_count"] -= 1
                    
                    return {
                        "status": "deleted",
                        "message": "Record deleted successfully",
                        "source": "csv"
                    }
            
            raise HTTPException(status_code=404, detail="Record not found")
        
        # Otherwise, try database table
        effective_db_url = db_url or default_db_url
        if not effective_db_url:
            raise HTTPException(status_code=400, detail="Database URL required for database tables")
            
        engine = get_db_engine(effective_db_url)
        table = get_table_schema(engine, table_name)
        
        with engine.connect() as conn:
            query = table.delete().where(table.c.id == record_id)
            result = conn.execute(query)
            conn.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Record not found")
            
            return {
                "status": "deleted",
                "message": "Record deleted successfully",
                "source": "database"
            }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete record: {str(e)}")

# GraphQL Schema
@strawberry.type
class Record:
    id: int
    table_name: str
    content: str  # JSON string representation of data

@strawberry.type
class Query:
    @strawberry.field
    def records(self, table_name: str, limit: int = 100, offset: int = 0) -> List[Record]:
        """Get records from a table"""
        # This would need to be implemented with actual database connection
        return []

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_record(self, table_name: str, content: str) -> Record:
        """Create a new record"""
        # This would need to be implemented with actual database connection
        return Record(id=1, table_name=table_name, content=content)

# Create GraphQL router
schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

# Mount GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
