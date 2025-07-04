document.addEventListener('DOMContentLoaded', () => {
    const jobListingsContainer = document.getElementById('jobListings');
    const applyModal = document.getElementById('applyModal');
    const modalJobTitle = document.getElementById('modalJobTitle');
    const applyForm = document.getElementById('applyForm');
    const cvFileInputModal = document.getElementById('cvFileInputModal');
    const modalStatus = document.getElementById('modalStatus');
    const closeButton = document.querySelector('.close-button');

    const API_BASE_URL = 'http://localhost:5000';
    let currentJobId = null;

    const toggleJobDetails = (jobCard) => {
        // Lấy thẻ div chứa mô tả
        const descriptionContainer = jobCard.querySelector('.job-description');
        
        // Thêm/xóa class 'active' để điều khiển việc hiển thị qua CSS
        jobCard.classList.toggle('active');

        // Nếu thẻ được mở ra và chưa có nội dung, chúng ta sẽ điền nội dung vào
        if (jobCard.classList.contains('active') && descriptionContainer.innerHTML === '') {
            let fullJd = jobCard.dataset.fullJd || 'Không có mô tả chi tiết.';
            
            // Áp dụng định dạng: thay ** bằng ' ' và * bằng '- '
            let formattedJd = fullJd
                .replace(/\*\*/g, ' ')
                .replace(/\*/g, '- ')
                .trim();

            descriptionContainer.innerText = formattedJd;
        }
    };

    const fetchAndRenderJobs = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/public/jobs`);
            if (!response.ok) throw new Error('Không thể tải danh sách việc làm.');
            const jobs = await response.json();

            jobListingsContainer.innerHTML = ''; // Clear old listings
            if (jobs.length === 0) {
                jobListingsContainer.innerHTML = '<p>Hiện tại chưa có vị trí nào đang tuyển dụng.</p>';
                return;
            }

            jobs.forEach(job => {
                const jobCard = document.createElement('div');
                jobCard.className = 'job-card';
                // Lưu JD đầy đủ vào data attribute để sử dụng sau
                jobCard.dataset.fullJd = job.job_description;

                jobCard.innerHTML = `
                    <div class="job-card-header">
                        <h3>${job.title}</h3>
                        <button class="icon-button apply-button" data-job-id="${job.id}" data-job-title="${job.title}">
                            <span class="material-icons">send</span> Ứng tuyển
                        </button>
                    </div>
                    <div class="job-description"></div>
                `;
                jobListingsContainer.appendChild(jobCard);

                // Thêm sự kiện click vào header của card để ẩn/hiện mô tả
                jobCard.querySelector('.job-card-header h3').addEventListener('click', () => {
                    toggleJobDetails(jobCard);
                });
            });
        } catch (error) {
            jobListingsContainer.innerHTML = `<p class="error">${error.message}</p>`;
        }
    };

    const openApplyModal = (jobId, jobTitle) => {
        currentJobId = jobId;
        modalJobTitle.textContent = `Ứng tuyển vị trí: ${jobTitle}`;
        applyModal.classList.remove('hidden');
    };

    const closeApplyModal = () => {
        applyModal.classList.add('hidden');
        applyForm.reset();
        modalStatus.classList.add('hidden');
        currentJobId = null;
    };

    // Event Listeners
    jobListingsContainer.addEventListener('click', (event) => {
        // Find the closest ancestor with class 'apply-button'
        const applyButton = event.target.closest('.apply-button');
        if (applyButton) {
            const { jobId, jobTitle } = applyButton.dataset;
            openApplyModal(jobId, jobTitle);
        }
    });

    closeButton.addEventListener('click', closeApplyModal);
    window.addEventListener('click', (event) => {
        if (event.target === applyModal) {
            closeApplyModal();
        }
    });

    applyForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const file = cvFileInputModal.files[0];
        if (!file || !currentJobId) {
            modalStatus.textContent = 'Vui lòng chọn file CV.';
            modalStatus.className = 'message error';
            modalStatus.classList.remove('hidden');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        modalStatus.textContent = 'Đang nộp hồ sơ...';
        modalStatus.className = 'message';
        modalStatus.classList.remove('hidden');

        try {
            const response = await fetch(`${API_BASE_URL}/public/jobs/${currentJobId}/apply`, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error);

            modalStatus.textContent = result.message;
            modalStatus.className = 'message';
            setTimeout(closeApplyModal, 2000); // Tự động đóng sau 2 giây
        } catch (error) {
            modalStatus.textContent = `Lỗi: ${error.message}`;
            modalStatus.className = 'message error';
        }
    });

    // Initial load
    fetchAndRenderJobs();
});