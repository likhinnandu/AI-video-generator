document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('generate-form');
    const submitBtn = document.getElementById('generate-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    
    const resultSection = document.getElementById('result-section');
    const errorSection = document.getElementById('error-section');
    const videoSource = document.getElementById('video-source');
    const outputVideo = document.getElementById('output-video');
    const downloadLink = document.getElementById('download-link');
    const errorMessage = document.getElementById('error-message');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 1. Prepare UI for loading
        document.body.classList.add('is-generating');
        submitBtn.disabled = true;
        btnText.textContent = 'Generating Masterpiece...';
        btnLoader.classList.remove('loader-hidden');
        
        resultSection.classList.add('hidden');
        errorSection.classList.add('hidden');

        // 2. Gather data
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        // Convert scenes to number
        data.scenes = parseInt(data.scenes, 10);

        try {
            // 3. Make API request
            const response = await fetch('/generate-video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || result.message || 'An error occurred during generation.');
            }

            // 4. Handle Success
            showResult(result);
            
        } catch (error) {
            // 5. Handle Error
            showError(error.message);
        } finally {
            // 6. Reset UI
            document.body.classList.remove('is-generating');
            submitBtn.disabled = false;
            btnText.textContent = 'Generate Video';
            btnLoader.classList.add('loader-hidden');
        }
    });

    function showResult(result) {
        // Set URLs
        videoSource.src = result.video_stream_url;
        downloadLink.href = result.video_download_url;
        
        // Load the video source explicitly required sometimes depending on browser flow
        outputVideo.load();
        
        // Show panel
        resultSection.classList.remove('hidden');
        
        // Scroll to results
        setTimeout(() => {
            resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorSection.classList.remove('hidden');
        
        setTimeout(() => {
            errorSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }
});
