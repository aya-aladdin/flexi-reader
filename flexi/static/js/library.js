document.addEventListener('DOMContentLoaded', () => {
    const bookGrid = document.getElementById('bookGrid');
    const editModal = document.getElementById('editBookModal');
    const editModalClose = document.querySelector('.close');
    const cancelEditModalBtn = document.getElementById('cancelEditModal');
    const editBookForm = document.getElementById('editBookForm');
    const editBookFormContent = document.getElementById('editBookFormContent');

    // Event delegation for the book grid
    bookGrid.addEventListener('click', (event) => {
        const target = event.target;
        const bookItem = target.closest('.book-item');
        const bookId = bookItem ? bookItem.dataset.bookId : null;

        if (!bookItem) {
            return; // Click was outside a book item
        }

        // Handle Details Button Click
        if (target.classList.contains('details-button')) {
            const detailsContainer = document.getElementById(`details-${bookId}`);
            if (detailsContainer) {
                detailsContainer.classList.toggle('show');
                event.stopPropagation();
            }
        }
        // Handle Delete Action (inside details container)
        else if (target.classList.contains('delete')) {
            const bookTitle = bookItem.querySelector('.book-title').textContent;
            if (confirm(`Are you sure you want to delete "${bookTitle}"?`)) {
                deleteBook(bookId, bookItem);
            }
        }
        // Handle Edit button click
        else if (target.classList.contains('edit')) {
            openEditModal(bookId);
        }
    });

    // Close details containers when clicking outside
    document.addEventListener('click', (event) => {
        const openDetails = document.querySelector('.details-container.show');
        if (openDetails && !openDetails.contains(event.target) && !event.target.classList.contains('details-button')) {
            openDetails.classList.remove('show');
        }
    });

    // Close the modal when the close button is clicked
    editModalClose.onclick = closeModal;
    cancelEditModalBtn.onclick = closeModal;

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target == editModal) {
            closeModal();
        }
    }

    // Function to delete a book
    function deleteBook(bookId, bookItem) {
        bookItem.classList.add('deleting'); // Add a class to visually indicate deleting

        fetch(`/delete_book/${bookId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                },
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                bookItem.remove(); // Remove the book item from the UI on success
                console.log('Book deleted successfully.');
            })
            .catch(error => {
                console.error('Error deleting book:', error);
                alert('Failed to delete the book. Please try again.');
            })
            .finally(() => {
                bookItem.classList.remove('deleting'); // Remove the deleting class whether success or failure
            });
    }

    // Function to open the edit modal
    function openEditModal(bookId) {
        fetch(`/get_edit_form/${bookId}/`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Populate the form fields in the modal
                const editBookFormContent = document.getElementById('editBookFormContent'); // Assuming you have an element with this ID
                const editModal = document.getElementById('editBookModal'); // Assuming you have an element with this ID

                if (!editBookFormContent || !editModal) {
                    console.error('Error: editBookFormContent or editModal element not found in the DOM.');
                    return;
                }

                editBookFormContent.innerHTML = `
            <form method="post" action="/upload_book/" enctype="multipart/form-data" class="upload-form" id="editBookForm">
                <input type="hidden" name="book_id" value="${bookId}">
                <div class="edit-form-group">
                    <label for="edit_title" class="edit-form-label">Title:</label>
                    <input type="text" class="edit-form-input" id="edit_title" name="title" value="${data.title}" required>
                    <div class="edit-form-error" id="title-error"></div>
                </div>
                <div class="form-group">
                    <label for="id_cover_image" class="form-label">Cover Image:</label>
                    <input type="file" class="form-control" id="id_cover_image" name="cover_image">
                    <div class="form-error" id="cover-image-error"></div>
                </div>
                <div class="form-group">
                    <label for="id_file" class="form-label">Book File:</label>
                    <input type="file" class="form-control" id="id_file" name="file" accept=".pdf">
                    <p class="form-help-text">Allowed format: .pdf</p>
                    <div class="form-error" id="file-error"></div>
                </div>
                <button type="submit" class="btn btn-primary">Save Changes</button>
            </form>
        `;
                editModal.style.display = "block";

                // Optional: You might want to add an event listener to the form here
                const editBookForm = document.getElementById('editBookForm');
                if (editBookForm) {
                    editBookForm.addEventListener('submit', function(event) {
                        event.preventDefault(); // Prevent default form submission

                        const formData = new FormData(this);
                        fetch(`/update_book/${bookId}/`, { // Assuming you have an update endpoint
                                method: 'POST',
                                headers: {
                                    'X-CSRFToken': getCookie('csrftoken'),
                                },
                                body: formData,
                            })
                            .then(response => {
                                if (!response.ok) {
                                    return response.text().then(text => {
                                        throw new Error(`HTTP error! Status: ${response.status} - ${text}`);
                                    });
                                }
                                return response.json();
                            })
                            .then(updatedData => {
                                console.log('Book updated successfully:', updatedData);
                                // Optionally update the UI with the new data
                                alert('Book updated successfully!');
                                editModal.style.display = "none"; // Close the modal
                                // You might want to refresh the book list here
                            })
                            .catch(error => {
                                console.error('Error updating book:', error);
                                alert(`Failed to update book: ${error.message}`);
                                // Optionally display specific error messages in the form
                            });
                    });
                }

            })
            .catch(error => {
                console.error('Error fetching edit form:', error);
                alert('Failed to load edit form.');
            });
    }

    // Helper function to get the CSRF token (assuming you have this defined elsewhere)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Function to initialize the edit form
    function initializeForm(bookId) {
        editBookForm.onsubmit = (event) => {
            event.preventDefault();

            const formData = new FormData(editBookForm);

            fetch(`/update_book/${bookId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: formData,
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Book updated successfully.');
                    closeModal();
                    window.location.href = "/library/"; // Refresh the page after a successful update
                })
                .catch(error => {
                    console.error('Error updating book:', error);
                    alert('Failed to update book. Please check the form and try again.');
                });
        };
    }

    function closeModal() {
        editModal.style.display = "none";
        editBookFormContent.innerHTML = '';
        editBookForm.onsubmit = null; // Remove the submit event listener
    }

    // Function to get CSRF token from cookies (for Django)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                let cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = cookie.substring(name.length + 1);
                    break;
                }
            }
        }
        return cookieValue;
    }
});