import React, { useState, useEffect } from "react";
import "./Home.css";

const Home = () => {
    const [books, setBooks] = useState([]);
    const [selectedBook, setSelectedBook] = useState(null);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [currentView, setCurrentView] = useState('list');
    const [imageFile, setImageFile] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);
    const [uploadedImageUrl, setUploadedImageUrl] = useState(null);
    const [uploadedImagePublicId, setUploadedImagePublicId] = useState(null);
    const [imageUploading, setImageUploading] = useState(false);
    const [shouldRemoveImage, setShouldRemoveImage] = useState(false);

    const [bookForm, setBookForm] = useState({
        title: '',
        author: '',
        isbn: '',
        publication_year: '',
        genre: '',
        description: '',
        available: false,
    });

    useEffect(() => {
        fetchBooks();
    }, []);

    const fetchBooks = async () => {
        setLoading(true);
        try {
            const response = await fetch(`http://localhost:8000/books/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            // Handle pagination response structure
            if (data.books && Array.isArray(data.books)) {
                setBooks(data.books);
            } else if (Array.isArray(data)) {
                setBooks(data);
            } else {
                setBooks([]);
            }
            setError('');
        } catch (err) {
            console.error('Error fetching books:', err);
            setError('Failed to get books');
            setBooks([]);
        }
        setLoading(false);
    };

    // Upload image to Cloudinary
    const uploadImageToCloudinary = async (imageFile) => {
        try {
            setImageUploading(true);
            const formData = new FormData();
            formData.append('file', imageFile);

            const response = await fetch(`http://localhost:8000/upload-image/`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                setUploadedImageUrl(data.image_url);
                setUploadedImagePublicId(data.image_public_id);
                setError('');
                return { image_url: data.image_url, public_id: data.image_public_id };
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to upload image');
                return null;
            }
        } catch (err) {
            console.error('Error uploading image:', err);
            setError('Failed to upload image');
            return null;
        } finally {
            setImageUploading(false);
        }
    };

    // Delete image from Cloudinary
    const deleteImageFromCloudinary = async (publicId) => {
        if (!publicId) return;
        
        try {
            const response = await fetch(`http://localhost:8000/delete-image/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ public_id: publicId }),
            });

            if (!response.ok) {
                console.error('Failed to delete image from Cloudinary');
            }
        } catch (err) {
            console.error('Error deleting image:', err);
        }
    };

    const addBook = async (bookData, imageUrl, imagePublicId) => {
        try {
            const bookPayload = {
                title: bookData.title,
                author: bookData.author,
                isbn: bookData.isbn,
                publication_year: parseInt(bookData.publication_year),
                genre: bookData.genre,
                description: bookData.description || null,
                available: Boolean(bookData.available),
                image_url: imageUrl || null,
                image_public_id: imagePublicId || null
            };

            console.log('Book payload being sent:', bookPayload);

            const response = await fetch(`http://localhost:8000/books/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(bookPayload),
            });

            if (response.ok) {
                fetchBooks();
                setError('');
                return true;
            } else {
                const errorData = await response.json();
                console.error('Server error:', errorData);
                
                // Handle validation errors properly
                if (errorData.detail && Array.isArray(errorData.detail)) {
                    const errorMessages = errorData.detail.map(err => `${err.loc?.join('.')}: ${err.msg}`).join(', ');
                    setError(`Validation errors: ${errorMessages}`);
                } else {
                    setError(errorData.detail || 'Failed to add book');
                }
            }
        } catch (err) {
            console.error('Network error:', err);
            setError('Failed to add book - Network error');
        }
        return false;
    };

    const updateBook = async (id, bookData, imageUrl, imagePublicId, shouldRemoveImage = false) => {
        try {
            const bookPayload = {
                title: bookData.title,
                author: bookData.author,
                isbn: bookData.isbn,
                publication_year: parseInt(bookData.publication_year),
                genre: bookData.genre,
                description: bookData.description || null,
                available: Boolean(bookData.available)
            };

            // Handle image updates - Fixed logic for image removal
            if (shouldRemoveImage) {
                // Explicitly set to null to remove image
                bookPayload.image_url = null;
                bookPayload.image_public_id = null;
            } else if (imageUrl && imagePublicId) {
                // Add new image
                bookPayload.image_url = imageUrl;
                bookPayload.image_public_id = imagePublicId;
            }
            // If neither condition is true, don't include image fields (keep existing)

            console.log('Update payload being sent:', bookPayload);

            const response = await fetch(`http://localhost:8000/books/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(bookPayload),
            });

            if (response.ok) {
                fetchBooks();
                setError('');
                return true;
            } else {
                const errorData = await response.json();
                console.error('Server error:', errorData);
                
                // Handle validation errors properly
                if (errorData.detail && Array.isArray(errorData.detail)) {
                    const errorMessages = errorData.detail.map(err => `${err.loc?.join('.')}: ${err.msg}`).join(', ');
                    setError(`Validation errors: ${errorMessages}`);
                } else {
                    setError(errorData.detail || 'Failed to update book');
                }
            }
        } catch (err) {
            console.error('Network error:', err);
            setError('Failed to update book - Network error');
        }
        return false;
    };

    const deleteBook = async (id) => {
        try {
            const response = await fetch(`http://localhost:8000/books/${id}`, {
                method: 'DELETE',
            });
            if (response.ok) {
                fetchBooks();
                setError('');
                return true;
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to delete book');
            }
        } catch (err) {
            console.error('Error deleting book:', err);
            setError('Failed to delete a book');
        }
        return false;
    };

    const handleAddClick = () => {
        setBookForm({
            title: '',
            author: '',
            isbn: '',
            publication_year: '',
            genre: '',
            description: '',
            available: false
        });
        setImageFile(null);
        setImagePreview(null);
        setUploadedImageUrl(null);
        setUploadedImagePublicId(null);
        setShouldRemoveImage(false);
        setCurrentView('add');
    };

    const handleEditClick = (book) => {
        setSelectedBook(book);
        setBookForm({
            title: book.title || '',
            author: book.author || '',
            isbn: book.isbn || '',
            publication_year: book.publication_year?.toString() || '',
            genre: book.genre || '',
            description: book.description || '',
            available: Boolean(book.available)
        });
        setImageFile(null);
        setImagePreview(book.image_url || null);
        setUploadedImageUrl(null);
        setUploadedImagePublicId(null);
        setShouldRemoveImage(false);
        setCurrentView('edit');
    };

    // New function to handle book view (description display)
    const handleViewClick = (book) => {
        setSelectedBook(book);
        setCurrentView('view');
    };

    const handleDeleteClick = (id) => {
        if (window.confirm('Are you sure you want to delete this book?')) {
            deleteBook(id);
        }
    };

    const handleFormSubmit = async (e) => {
        e.preventDefault();
        console.log('Form data before submit:', bookForm);
        
        // Validate required fields
        if (!bookForm.title || !bookForm.author || !bookForm.isbn || !bookForm.publication_year || !bookForm.genre) {
            setError('Please fill in all required fields');
            return;
        }

        // Validate publication year
        const year = parseInt(bookForm.publication_year);
        if (isNaN(year) || year < 1000 || year > new Date().getFullYear() + 10) {
            setError('Please enter a valid publication year');
            return;
        }

        let success = false;
        let finalImageUrl = uploadedImageUrl;
        let finalImagePublicId = uploadedImagePublicId;

        // If there's a new image file that hasn't been uploaded yet, upload it first
        if (imageFile && !uploadedImageUrl) {
            const uploadResult = await uploadImageToCloudinary(imageFile);
            if (uploadResult) {
                finalImageUrl = uploadResult.image_url;
                finalImagePublicId = uploadResult.public_id;
            } else {
                return; // Stop if image upload failed
            }
        }

        if (currentView === 'add') {
            success = await addBook(bookForm, finalImageUrl, finalImagePublicId);
        } else if (currentView === 'edit') {
            success = await updateBook(
                selectedBook._id, 
                bookForm, 
                finalImageUrl, 
                finalImagePublicId, 
                shouldRemoveImage
            );
        }

        if (success) {
            setCurrentView('list');
            setSelectedBook(null);
            setImageFile(null);
            setImagePreview(null);
            setUploadedImageUrl(null);
            setUploadedImagePublicId(null);
            setShouldRemoveImage(false);
        } else {
            // If book creation/update failed and we just uploaded an image, delete it
            if (finalImageUrl && finalImagePublicId) {
                await deleteImageFromCloudinary(finalImagePublicId);
                setUploadedImageUrl(null);
                setUploadedImagePublicId(null);
            }
        }
    };

    const handleCancel = async () => {
        // If user cancels and there's a newly uploaded image in this session, delete it
        if (uploadedImagePublicId) {
            await deleteImageFromCloudinary(uploadedImagePublicId);
        }
        
        setCurrentView('list');
        setSelectedBook(null);
        setImageFile(null);
        setImagePreview(null);
        setUploadedImageUrl(null);
        setUploadedImagePublicId(null);
        setShouldRemoveImage(false);
    };

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        const newValue = type === 'checkbox' ? checked : value;
        setBookForm({ ...bookForm, [name]: newValue });
    };

    const handleImageChange = async (e) => {
        const file = e.target.files[0];
        if (file) {
            if (!file.type.startsWith('image/')) {
                setError('Please select a valid image file');
                return;
            }
            
            if (file.size > 5 * 1024 * 1024) {
                setError('Image file size should be less than 5MB');
                return;
            }

            // If there's a previously uploaded image in this session, delete it
            if (uploadedImagePublicId) {
                await deleteImageFromCloudinary(uploadedImagePublicId);
            }

            // Reset remove flag since we're adding a new image
            setShouldRemoveImage(false);

            setImageFile(file);
            
            // Create preview
            const reader = new FileReader();
            reader.onload = (e) => {
                setImagePreview(e.target.result);
            };
            reader.readAsDataURL(file);
            setError('');

            // Upload new image to Cloudinary
            const uploadResult = await uploadImageToCloudinary(file);
            if (!uploadResult) {
                // If upload failed, reset the image
                setImageFile(null);
                setImagePreview(null);
                const fileInput = document.getElementById('image-input');
                if (fileInput) {
                    fileInput.value = '';
                }
            }
        }
    };

    const removeImage = async () => {
        // If there's a newly uploaded image in this session, delete it from Cloudinary
        if (uploadedImagePublicId) {
            await deleteImageFromCloudinary(uploadedImagePublicId);
        }
        
        // Set flag to indicate image should be removed when updating
        setShouldRemoveImage(true);
        
        setImageFile(null);
        setImagePreview(null);
        setUploadedImageUrl(null);
        setUploadedImagePublicId(null);
        
        const fileInput = document.getElementById('image-input');
        if (fileInput) {
            fileInput.value = '';
        }
    };

    const filteredBooks = (books || []).filter(book =>
        (book.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (book.author || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (book.genre || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="home-container">
            <h1>Library Management System</h1>

            {error && <div className="error-message">{typeof error === 'string' ? error : JSON.stringify(error)}</div>}
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
                        <div className="books-grid">
                            {filteredBooks.map((book) => (
                                <div key={book._id} className="book-card">
                                    {book.image_url && (
                                        <div className="book-image">
                                            <img src={book.image_url} alt={book.title} />
                                        </div>
                                    )}
                                    <div className="book-details">
                                        <h3 
                                            onClick={() => handleViewClick(book)}
                                            style={{ cursor: 'pointer', color: '#007bff' }}
                                            title="Click to view details"
                                        >
                                            {book.title}
                                        </h3>
                                        <p><strong>Author:</strong> {book.author}</p>
                                        <p><strong>ISBN:</strong> {book.isbn}</p>
                                        <p><strong>Year:</strong> {book.publication_year}</p>
                                        <p><strong>Genre:</strong> {book.genre}</p>
                                        <p><strong>Available:</strong> {book.available ? 'Yes' : 'No'}</p>
                                        <div className="book-actions">
                                            <button 
                                                onClick={() => handleViewClick(book)}
                                                className="view-button"
                                                style={{ backgroundColor: '#17a2b8', color: 'white', marginRight: '5px' }}
                                            >
                                                View
                                            </button>
                                            <button 
                                                onClick={() => handleEditClick(book)}
                                                className="edit-button"
                                            >
                                                Edit
                                            </button>
                                            <button 
                                                onClick={() => handleDeleteClick(book._id)}
                                                className="delete-button"
                                            >
                                                Delete
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Book Detail View */}
            {currentView === 'view' && selectedBook && (
                <div className="book-detail-view">
                    <div className="detail-header">
                        <button 
                            onClick={() => setCurrentView('list')}
                            className="back-button"
                            style={{ marginBottom: '20px', padding: '8px 16px' }}
                        >
                            ← Back to List
                        </button>
                        <h2>{selectedBook.title}</h2>
                    </div>
                    
                    <div className="book-detail-content">
                        {selectedBook.image_url && (
                            <div className="detail-image">
                                <img src={selectedBook.image_url} alt={selectedBook.title} style={{ maxWidth: '300px', maxHeight: '400px' }} />
                            </div>
                        )}
                        
                        <div className="detail-info">
                            <p><strong>Author:</strong> {selectedBook.author}</p>
                            <p><strong>ISBN:</strong> {selectedBook.isbn}</p>
                            <p><strong>Publication Year:</strong> {selectedBook.publication_year}</p>
                            <p><strong>Genre:</strong> {selectedBook.genre}</p>
                            <p><strong>Available:</strong> {selectedBook.available ? 'Yes' : 'No'}</p>
                            
                            {selectedBook.description && (
                                <div className="description-section" style={{ marginTop: '20px' }}>
                                    <h3>Description:</h3>
                                    <p style={{ lineHeight: '1.6', textAlign: 'justify' }}>
                                        {selectedBook.description}
                                    </p>
                                </div>
                            )}
                            
                            <div className="detail-actions" style={{ marginTop: '20px' }}>
                                <button 
                                    onClick={() => handleEditClick(selectedBook)}
                                    className="edit-button"
                                    style={{ marginRight: '10px' }}
                                >
                                    Edit Book
                                </button>
                                <button 
                                    onClick={() => handleDeleteClick(selectedBook._id)}
                                    className="delete-button"
                                >
                                    Delete Book
                                </button>
                            </div>
                        </div>
                    </div>
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
                                type="number"
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
                            <label>Description:</label>
                            <textarea
                                name="description"
                                value={bookForm.description}
                                onChange={handleInputChange}
                                rows="4"
                                placeholder="Enter book description (optional)"
                                style={{ width: '100%', resize: 'vertical' }}
                            />
                        </div>
                        
                        <div className="form-group">
                            <label>
                                <input
                                    type="checkbox"
                                    name="available"
                                    checked={bookForm.available}
                                    onChange={(e) =>
                                        setBookForm({ ...bookForm, available: e.target.checked })
                                    }
                                />
                                Available
                            </label>
                        </div>

                        <div className="form-group">
                            <label>Book Cover Image:</label>
                            <input
                                id="image-input"
                                type="file"
                                accept="image/*"
                                onChange={handleImageChange}
                                className="image-input"
                                disabled={imageUploading}
                            />
                            <small className="form-text">
                                Supported formats: JPG, PNG, GIF. Max size: 5MB
                                {imageUploading && " - Uploading..."}
                            </small>
                        </div>

                        {imageUploading && (
                            <div className="uploading-message">
                                Uploading image to Cloudinary...
                            </div>
                        )}

                        {imagePreview && (
                            <div className="image-preview">
                                <img src={imagePreview} alt="Preview" />
                                <button 
                                    type="button" 
                                    onClick={removeImage}
                                    className="remove-image-button"
                                    disabled={imageUploading}
                                >
                                    Remove Image
                                </button>
                                {uploadedImageUrl && (
                                    <div className="upload-status">
                                        ✅ Image uploaded successfully
                                    </div>
                                )}
                                {shouldRemoveImage && (
                                    <div className="remove-status" style={{ color: 'red' }}>
                                        ⚠️ Image will be removed when you save
                                    </div>
                                )}
                            </div>
                        )}

                        <div className="form-buttons">
                            <button 
                                type="submit" 
                                className="save-button"
                                disabled={imageUploading}
                            >
                                {currentView === 'add' ? 'Add Book' : 'Update Book'}
                            </button>
                            <button 
                                type="button" 
                                onClick={handleCancel} 
                                className="cancel-button"
                                disabled={imageUploading}
                            >
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