from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.database.connection import get_db_connection, init_db
from mysql.connector import Error
from contextlib import asynccontextmanager


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: Optional[bool] = False


class TaskCreate(TaskBase):
    pass


class Task(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Task Management API",
    description="A Rosetta Stone CRUD API for managing tasks",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Task Management API. Visit /docs for the API documentation."}


@app.get("/ask")
async def ask_valentine():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Be My Valentine?</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin: 50px; }
            #message { font-size: 24px; margin-bottom: 20px; }
            .buttons { display: flex; justify-content: center; gap: 20px; }
            button { font-size: 20px; padding: 10px 20px; cursor: pointer; }
            #yes-btn { font-size: 20px; }
            #no-btn { font-size: 20px; }
            #happy-cat { display: none; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div id="message">Will you be my Valentine?</div>
        <div class="buttons">
            <button id="yes-btn" onclick="acceptValentine()">Yes</button>
            <button id="no-btn" onclick="increaseYesSize()">No</button>
        </div>
        <img id="happy-cat" src="https://c.tenor.com/8D79eXbqSP8AAAAC/cute-cat.gif" alt="Happy Cat">
        <script>
            let yesSize = 20;
            let noSize = 20;
            const messages = [
                "Are you sure? 😢",
                "Come on, think again! 🥺",
                "You're breaking my heart 💔",
                "Please reconsider! 🥹",
                "This is your last chance! 😭"
            ];
            let msgIndex = 0;

            function increaseYesSize() {
                yesSize += 10;
                noSize -= 2;
                document.getElementById('yes-btn').style.fontSize = yesSize + 'px';
                document.getElementById('no-btn').style.fontSize = Math.max(noSize, 10) + 'px';
                if (msgIndex < messages.length) {
                    document.getElementById('message').innerText = messages[msgIndex];
                    msgIndex++;
                } else {
                    document.getElementById('message').innerText = "There's no escape! Say yes! 😈";
                }
            }

            function acceptValentine() {
                document.getElementById('message').innerText = "I knew you would accept! ❤️";
                document.querySelector('.buttons').style.display = 'none';
                document.getElementById('happy-cat').style.display = 'block';
            }
        </script>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")


@app.post("/tasks/", response_model=Task)
async def create_task(task: TaskCreate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        query = "INSERT INTO tasks (title, description, completed) VALUES (%s, %s, %s)"
        values = (task.title, task.description, task.completed)
        cursor.execute(query, values)
        conn.commit()

        # Get the created task
        task_id = cursor.lastrowid
        cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        new_task = cursor.fetchone()
        return new_task
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/tasks/", response_model=List[Task])
async def read_tasks():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks")
        tasks = cursor.fetchall()
        return tasks
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/tasks/{task_id}", response_model=Task)
async def read_task(task_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task: TaskCreate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
        UPDATE tasks 
        SET title = %s, description = %s, completed = %s
        WHERE id = %s
        """
        values = (task.title, task.description, task.completed, task_id)
        cursor.execute(query, values)
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")

        cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        updated_task = cursor.fetchone()
        return updated_task
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")

        return {"message": "Task deleted successfully"}
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
