import React, { useState, useEffect } from "react";
import "./Home.css";

const Home=() =>{
    const [books,setBooks]= useState([]);
    const [selectedBook,setSelectedBook]=useState(null);
    const [error,setError]=useState('');
    const [loading, setLoading]= useState(false);
    const [searchTerm, setSearchTerm]=useState('');
    const [currentView, setCurrentView]=useState('list');

    const [bookForm,setBookForm]=useState({
        title:'',
        author:'',
        isbn:'',
        publication_year:'',
        genre:'',
        available:false,
    });

    useEffect(()=>{
        fetchBooks();
    },[]);

    const fetchBooks= async ()=>{
        setLoading(true);
        try{
            const response =await fetch(`http://localhost:8000/books`);
            const data = await response.json();
            setBooks(Array.isArray(data)?data:[]);
            setError('');
        }
        catch(err){
            setError('Failed to get books');
            setBooks([]);
        }
        setLoading(false);
    };

    const addBook= async (bookData)=>{
        try{
            const dataToSend={
              ...bookData,
              publication_year: parseInt(bookData.publication_year),
              available:Boolean(bookData.available==="true"),
            };
            const response=await fetch(`http://localhost:8000/books`,{
            method:'POST',
            headers:{
                'Content-Type':'application/json',
            },
            body:JSON.stringify(dataToSend),
            });
            if(response.ok){
                fetchBooks();
                setError('');
                return true;
            }
        }catch(err){
            setError('failed to add book');
        }
        return false;
    };

    const updateBook = async(id, bookData)=>{
        try{
            const response= await fetch(`http://localhost:8000/books/${id}`,{
                method:'PUT',
                headers:{
                    'Content-Type':'application/json',
                },
                body:JSON.stringify(bookData),
            });
            if(response.ok){
                fetchBooks();
                setError('');
                return true;
            }
        } catch(err){
            setError('failed to update book');
        }
        return false;
    };

    const deleteBook= async(id)=>{
        try{
            const response= await fetch(`http://localhost:8000/books/${id}`,{
                method:'DELETE',
            });
            if(response.ok){
                fetchBooks();
                setError('');
                return true;
            }
        } catch(err){
            setError('failed to delete a book');
        }
        return false;
    };


    const handleAddClick=()=>{
        setBookForm({
            title:'',
            author:'',
            isbn:'',
            publication_year:'',
            genre:'',
            available:''
        });
        setCurrentView('add');
    };

    const handleEditClick=(book)=>{
        setSelectedBook(book);
        setBookForm(book);
        setCurrentView('edit');
    };

    const handleDeleteClick=(id)=>{
        if(window.confirm('Are you sure you want to delete this book?')){
            deleteBook(id);
        }
    };

    const handleFormSubmit=async(e)=>{
        e.preventDefault();
        console.log('Form data before submit:',bookForm);
        let success=false;

        if(currentView==='add'){
            success=await addBook(bookForm);
        } else if(currentView==='edit'){
            success=await updateBook(selectedBook.id,bookForm);
        }

        if(success){
            setCurrentView('list');
            setSelectedBook(null);
        }
    };

    const handleCancel=()=>{
        setCurrentView('list');
        setSelectedBook(null);
    };


    const handleInputChange=(e)=>{
        setBookForm({
            ...bookForm,
            [e.target.name]:e.target.value
        });
    };

    const filteredBooks=(books || []).filter(book =>
        book.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        book.author.toLowerCase().includes(searchTerm.toLowerCase()) ||
        book.genre.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return(
        <div className="home-container">
            <h1>library Management System</h1>

            {error && <div className="error-message">{error}</div>}
            <div className="top-controls">
            <input
             type="text"
             placeholder="Search books by title, author, or genre..."
             value={searchTerm}
             onChange={(e) => setSearchTerm(e.target.value)}
             className="search-input"
            />
            {currentView === 'list' && (
            <button onClick={handleAddClick} className="add-button">
                Add New Book
            </button>
            )}
        </div>

      {loading && <div className="loading">Loading books...</div>}

      {/* Book List View */}
      {currentView === 'list' && !loading && (
        <div className="book-list">
          <h2>Books ({filteredBooks.length})</h2>
          {filteredBooks.length === 0 ? (
            <p>No books found.</p>
          ) : (
            <table className="books-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Author</th>
                  <th>ISBN</th>
                  <th>Year</th>
                  <th>Genre</th>
                  <th>Available</th>
                </tr>
              </thead>
              <tbody>
                {filteredBooks.map((book) => (
                  <tr key={book.id}>
                    <td>{book.title}</td>
                    <td>{book.author}</td>
                    <td>{book.isbn}</td>
                    <td>{book.publication_year}</td>
                    <td>{book.genre}</td>
                    <td>{book.available ? 1 : 0}</td>
                    <td>
                      <button 
                        onClick={() => handleEditClick(book)}
                        className="edit-button"
                      >
                        Edit
                      </button>
                      <button 
                        onClick={() => handleDeleteClick(book.id)}
                        className="delete-button"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Add/Edit Form View */}
      {(currentView === 'add' || currentView === 'edit') && (
        <div className="form-container">
          <h2>{currentView === 'add' ? 'Add New Book' : 'Edit Book'}</h2>
          <form onSubmit={handleFormSubmit} className="book-form">
            <div className="form-group">
              <label>Title:</label>
              <input
                type="text"
                name="title"
                value={bookForm.title}
                onChange={handleInputChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label>Author:</label>
              <input
                type="text"
                name="author"
                value={bookForm.author}
                onChange={handleInputChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label>ISBN:</label>
              <input
                type="text"
                name="isbn"
                value={bookForm.isbn}
                onChange={handleInputChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label>Published Year:</label>
              <input
                type="text"
                name="publication_year"
                value={bookForm.publication_year}
                onChange={handleInputChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label>Genre:</label>
              <input
                type="text"
                name="genre"
                value={bookForm.genre}
                onChange={handleInputChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label>Available:</label>
              <input
                type="checkbox"
                name="available"
                checked={bookForm.available}
                onChange={(e) =>
                  setBookForm({ ...bookForm, available: e.target.checked })
                }
              />
            </div>

            
            <div className="form-buttons">
              <button type="submit" className="save-button">
                {currentView === 'add' ? 'Add Book' : 'Update Book'}
              </button>
              <button type="button" onClick={handleCancel} className="cancel-button">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default Home;
         
