from typing import Annotated
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from fastapi import FastAPI, Depends, HTTPException
from models.book import Book
from sqlalchemy import select

app = FastAPI()

engine = create_async_engine("sqlite+aiosqlite:///books.db")


new_session = async_sessionmaker(engine, expire_on_commit=True)


async def get_session():
    async with new_session() as session:
        yield session


DepSession = Annotated[AsyncSession, Depends(get_session)]


class Base(DeclarativeBase):
    pass


class BookModel(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author: Mapped[str]
    description: Mapped[str] = mapped_column(default=None, nullable=True)


@app.post("/create-database")
async def create_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"message": "Success"}


@app.post("/add/book")
async def add_book(book: Book, session: DepSession):
    new_book = BookModel(
        title=book.title, author=book.author, description=book.description
    )
    session.add(new_book)
    await session.commit()
    await session.refresh(new_book)
    return new_book


@app.get("/get/books")
async def get_books(session: DepSession):
    query = select(BookModel)
    books = await session.execute(query)
    return books.scalars().all()


@app.get("/get/{book_id}")
async def get_book(book_id: int, session: DepSession):
    book = await session.get(BookModel, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Not Found")
    return book


@app.put("/update/book")
async def update_book(book_id: int, data: Book, session: DepSession):
    book = await session.get(BookModel, book_id)
    if not book:
        HTTPException(status_code=404, detail="Not Found")

    book.title = data.title
    book.author = data.author
    book.description = data.description
    await session.commit()
    await session.refresh(book) 
    return book

@app.delete("/delete/{book_id}")
async def delete_book(book_id: int, session: DepSession):
    book = await session.get(BookModel, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Not Found")
    await session.delete(book)
    await session.commit()
    return {"ok": True}