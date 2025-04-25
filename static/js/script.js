// Wait for the DOM to be loaded
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Validate file input to ensure only Excel files are selected
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.value.toLowerCase();
            const validExtensions = ['.xlsx', '.xls'];
            let isValid = false;
            
            for (let ext of validExtensions) {
                if (fileName.endsWith(ext)) {
                    isValid = true;
                    break;
                }
            }
            
            if (!isValid && fileName) {
                alert('Please select a valid Excel file (.xlsx or .xls)');
                this.value = ''; // Clear the file input
            }
        });
    }
});
