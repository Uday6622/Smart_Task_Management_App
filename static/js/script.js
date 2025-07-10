// scripts.js

document.addEventListener("DOMContentLoaded", function () {
    console.log("Smart Task Management App loaded.");

    // Example: confirm before deleting
    const deleteButtons = document.querySelectorAll(".delete-task");
    deleteButtons.forEach(function (button) {
        button.addEventListener("click", function (event) {
            if (!confirm("Are you sure you want to delete this task?")) {
                event.preventDefault();
            }
        });
    });
});
