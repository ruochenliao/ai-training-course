from dotenv import load_dotenv

load_dotenv()

from functools import wraps
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import os
import json
import pandas as pd
from pydantic import BaseModel
from cache import MemoryCache

app = FastAPI(title="Vanna API", description="API for Vanna")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# SETUP
cache = MemoryCache()

from database import SQLiteDatabase

vn = SQLiteDatabase()
vn.connect_to_sqlite('https://vanna.ai/Chinook.sqlite')


# Pydantic models for request and response validation
class TrainingDataRequest(BaseModel):
    question: Optional[str] = None
    sql: Optional[str] = None
    ddl: Optional[str] = None
    documentation: Optional[str] = None

class RemoveTrainingDataRequest(BaseModel):
    id: str

# Helper function to check cache and return field values
async def get_cache_fields(id: str, fields: List[str]):
    if id is None:
        raise HTTPException(status_code=400, detail="No id provided")

    for field in fields:
        if cache.get(id=id, field=field) is None:
            raise HTTPException(status_code=404, detail=f"No {field} found")

    field_values = {field: cache.get(id=id, field=field) for field in fields}
    field_values['id'] = id

    return field_values


@app.get('/api/v0/generate_questions')
async def generate_questions():
    return {
        "type": "question_list",
        "questions": vn.generate_questions(),
        "header": "Here are some questions you can ask:"
    }


@app.get('/api/v0/generate_sql')
async def generate_sql(question: Optional[str] = None):
    if question is None:
        raise HTTPException(status_code=400, detail="No question provided")

    id = cache.generate_id(question=question)
    sql = vn.generate_sql(question=question)

    cache.set(id=id, field='question', value=question)
    cache.set(id=id, field='sql', value=sql)

    return {
        "type": "sql",
        "id": id,
        "text": sql,
    }


@app.get('/api/v0/run_sql')
async def run_sql(id: str):
    try:
        # Get required fields from cache
        cache_data = await get_cache_fields(id, ['sql'])
        sql = cache_data['sql']

        df = vn.run_sql(sql=sql)

        cache.set(id=id, field='df', value=df)

        return {
            "type": "df",
            "id": id,
            "df": df.head(10).to_json(orient='records'),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/v0/download_csv')
async def download_csv(id: str):
    # Get required fields from cache
    cache_data = await get_cache_fields(id, ['df'])
    df = cache_data['df']

    csv = df.to_csv()

    return Response(
        content=csv,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={id}.csv"}
    )


@app.get('/api/v0/generate_plotly_figure')
async def generate_plotly_figure(id: str):
    try:
        # Get required fields from cache
        cache_data = await get_cache_fields(id, ['df', 'question', 'sql'])
        df = cache_data['df']
        question = cache_data['question']
        sql = cache_data['sql']

        code = vn.generate_plotly_code(
            question=question,
            sql=sql,
            df_metadata=f"Running df.dtypes gives:\n {df.dtypes}"
        )
        fig = vn.get_plotly_figure(plotly_code=code, df=df, dark_mode=False)
        fig_json = fig.to_json()

        cache.set(id=id, field='fig_json', value=fig_json)

        return {
            "type": "plotly_figure",
            "id": id,
            "fig": fig_json,
        }
    except HTTPException:
        raise
    except Exception as e:
        # Print the stack trace
        import traceback
        traceback.print_exc()

        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/v0/get_training_data')
async def get_training_data():
    df = vn.get_training_data()

    return {
        "type": "df",
        "id": "training_data",
        "df": df.head(25).to_json(orient='records'),
    }


@app.post('/api/v0/remove_training_data')
async def remove_training_data(request: RemoveTrainingDataRequest):
    if request.id is None:
        raise HTTPException(status_code=400, detail="No id provided")

    if vn.remove_training_data(id=request.id):
        return {"success": True}
    else:
        raise HTTPException(status_code=500, detail="Couldn't remove training data")


@app.post('/api/v0/train')
async def add_training_data(request: TrainingDataRequest):
    try:
        id = vn.train(
            question=request.question,
            sql=request.sql,
            ddl=request.ddl,
            documentation=request.documentation
        )

        return {"id": id}
    except Exception as e:
        print("TRAINING ERROR", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/v0/generate_followup_questions')
async def generate_followup_questions(id: str):
    # Get required fields from cache
    cache_data = await get_cache_fields(id, ['df', 'question', 'sql'])
    df = cache_data['df']
    question = cache_data['question']
    sql = cache_data['sql']

    followup_questions = vn.generate_followup_questions(question=question, sql=sql, df=df)

    cache.set(id=id, field='followup_questions', value=followup_questions)

    return {
        "type": "question_list",
        "id": id,
        "questions": followup_questions,
        "header": "Here are some followup questions you can ask:"
    }


@app.get('/api/v0/load_question')
async def load_question(id: str):
    try:
        # Get required fields from cache
        cache_data = await get_cache_fields(id, ['question', 'sql', 'df', 'fig_json', 'followup_questions'])
        question = cache_data['question']
        sql = cache_data['sql']
        df = cache_data['df']
        fig_json = cache_data['fig_json']
        followup_questions = cache_data['followup_questions']

        return {
            "type": "question_cache",
            "id": id,
            "question": question,
            "sql": sql,
            "df": df.head(10).to_json(orient='records'),
            "fig": fig_json,
            "followup_questions": followup_questions,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/v0/get_question_history')
async def get_question_history():
    return {"type": "question_history", "questions": cache.get_all(field_list=['question'])}


@app.get('/')
async def root():
    return FileResponse('static/index.html')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)