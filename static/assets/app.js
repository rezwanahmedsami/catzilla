
    // Catzilla Static Files Demo JavaScript
    console.log('🌪️ Catzilla Static Files Loaded!');

    document.addEventListener('DOMContentLoaded', function() {
        // Add loading animation
        const cards = document.querySelectorAll('.file-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';

            setTimeout(() => {
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });

        // Add download tracking
        const downloadLinks = document.querySelectorAll('.download-btn');
        downloadLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const filename = this.dataset.filename;
                console.log(`Downloading: ${filename}`);

                // Track download
                fetch('/api/track-download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        filename: filename,
                        timestamp: new Date().toISOString()
                    })
                });
            });
        });
    });

    // File upload drag and drop
    function setupFileUpload() {
        const dropZone = document.getElementById('dropZone');
        if (!dropZone) return;

        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            console.log('Files dropped:', files.length);
        });
    }

    setupFileUpload();
