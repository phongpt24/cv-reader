document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const createJobForm = document.getElementById('createJobForm');
    const recruiterJobList = document.getElementById('recruiterJobList');
    const applicantSection = document.getElementById('applicantSection');
    const applicantListTitle = document.getElementById('applicantListTitle');
    const applicantTableBody = document.getElementById('applicantTableBody');
    const aiProfileModal = document.getElementById('aiProfileModal');
    const closeProfileModalBtn = aiProfileModal.querySelector('.profile-close');
    
    // New elements for showing/hiding the form
    const showCreateJobFormBtn = document.getElementById('showCreateJobFormBtn');
    const createJobCard = document.getElementById('createJobCard');

    const API_BASE_URL = 'http://localhost:5000';
    let currentJobFolder = null;

    // === FUNCTIONS FOR JOB MANAGEMENT ===
    const fetchAndRenderRecruiterJobs = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/recruiter/jobs`);
            const jobs = await response.json();
            recruiterJobList.innerHTML = '';
            jobs.forEach(job => {
                const li = document.createElement('li');
                li.dataset.jobId = job.id;
                li.dataset.jobTitle = job.title;
                li.innerHTML = `
                    <span>${job.title}</span>
                    <button class="delete-job-btn material-icons" data-job-id="${job.id}">delete_forever</button>
                `;
                recruiterJobList.appendChild(li);
            });
        } catch (error) {
            console.error("Lỗi khi tải tin tuyển dụng:", error);
        }
    };

    // Event listener for the new button
    showCreateJobFormBtn.addEventListener('click', () => {
        createJobCard.classList.toggle('hidden');
    });

    createJobForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const title = document.getElementById('jobTitle').value;
        const jd = document.getElementById('jobDescription').value;
        
        try {
            const response = await fetch(`${API_BASE_URL}/recruiter/jobs`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, jd })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error);
            alert(result.message);
            createJobForm.reset();
            createJobCard.classList.add('hidden'); // Hide the form after submission
            fetchAndRenderRecruiterJobs(); // Refresh the list
        } catch (error) {
            alert(`Lỗi: ${error.message}`);
        }
    });

    recruiterJobList.addEventListener('click', async (event) => {
        const target = event.target;
        if (target.tagName === 'SPAN' && target.closest('li')) { // Click vào tên job để xem ứng viên
            const li = target.closest('li');
            const jobId = li.dataset.jobId;
            const jobTitle = li.dataset.jobTitle;
            
            // Highlight selected job
            document.querySelectorAll('#recruiterJobList li').forEach(liItem => liItem.classList.remove('active'));
            li.classList.add('active');

            fetchAndRenderApplicants(jobId, jobTitle);
        } else if (target.classList.contains('delete-job-btn')) { // Click vào nút xóa
            const jobId = target.dataset.jobId;
            const jobTitle = target.closest('li').querySelector('span').textContent; // Lấy tiêu đề job
            if (confirm(`Bạn có chắc chắn muốn xóa tin tuyển dụng "${jobTitle}" và tất cả ứng viên liên quan không? Hành động này không thể hoàn tác.`)) {
                await deleteJobPosting(jobId);
            }
        }
    });

    const deleteJobPosting = async (jobId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/recruiter/jobs/${jobId}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error);
            alert(result.message);
            fetchAndRenderRecruiterJobs(); // Tải lại danh sách job
            applicantSection.classList.add('hidden'); // Ẩn danh sách ứng viên nếu job bị xóa
        } catch (error) {
            alert(`Lỗi khi xóa tin tuyển dụng: ${error.message}`);
            console.error("Lỗi khi xóa tin tuyển dụng:", error);
        }
    };

    // === FUNCTIONS FOR APPLICANT MANAGEMENT ===
    const fetchAndRenderApplicants = async (jobId, jobTitle) => {
        applicantListTitle.textContent = `Ứng viên cho vị trí: ${jobTitle}`;
        try {
            const response = await fetch(`${API_BASE_URL}/recruiter/jobs/${jobId}/candidates`);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error);
            
            currentJobFolder = data.job_folder; // Lưu lại folder
            const candidates = data.candidates;
            const statuses = ['Mới', 'Đã xem', 'Phù hợp', 'Không phù hợp', 'Phỏng vấn'];

            applicantTableBody.innerHTML = '';
            if (candidates.length === 0) {
                applicantTableBody.innerHTML = '<tr><td colspan="4">Chưa có ứng viên nào.</td></tr>';
            } else {
                candidates.forEach(candidate => {
                    const tr = document.createElement('tr');
                    
                    const statusOptions = statuses.map(status => 
                        `<option value="${status}" ${candidate.status === status ? 'selected' : ''}>${status}</option>`
                    ).join('');

                    tr.innerHTML = `
                        <td>${candidate.full_name}</td>
                        <td><span class="score-badge">${candidate.match_score}%</span></td>
                        <td>
                            <select class="status-select" data-candidate-id="${candidate.id}">
                                ${statusOptions}
                            </select>
                        </td>
                        <td class="action-buttons">
                            <button class="icon-button view-profile-button" data-candidate-id="${candidate.id}">
                                <span class="material-icons">visibility</span> Xem hồ sơ
                            </button>
                            <a href="${API_BASE_URL}/public/download_cv/${currentJobFolder}/${candidate.cv_file_path}" target="_blank" class="icon-button download-cv-button">
                                <span class="material-icons">download</span> Tải CV
                            </a>
                        </td>
                    `;
                    applicantTableBody.appendChild(tr);
                });
            }
            applicantSection.classList.remove('hidden');
        } catch (error) {
            console.error("Lỗi khi tải ứng viên:", error);
            applicantSection.classList.add('hidden');
        }
    };

    const updateCandidateStatus = async (candidateId, newStatus, selectElement) => {
        try {
            const response = await fetch(`${API_BASE_URL}/recruiter/candidates/${candidateId}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: newStatus })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error);
            
            selectElement.style.border = '2px solid #28a745';
            setTimeout(() => {
                selectElement.style.border = '';
            }, 2000);

        } catch (error) {
            alert(`Lỗi khi cập nhật trạng thái: ${error.message}`);
            selectElement.style.border = '2px solid #dc3545';
             setTimeout(() => {
                selectElement.style.border = ''; 
            }, 2000);
        }
    };
    
    applicantTableBody.addEventListener('click', event => {
        const target = event.target;
        // Check if the clicked element or its parent is a .view-profile-button
        const viewProfileButton = target.closest('.view-profile-button');
        if(viewProfileButton) {
            const candidateId = viewProfileButton.dataset.candidateId;
            openAiProfileModal(candidateId);
        }
    });

    applicantTableBody.addEventListener('change', event => {
        const target = event.target;
        if (target.classList.contains('status-select')) {
            const candidateId = target.dataset.candidateId;
            const newStatus = target.value;
            updateCandidateStatus(candidateId, newStatus, target);
        }
    });
    
    // === AI PROFILE MODAL LOGIC ===
    const openAiProfileModal = async (candidateId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/recruiter/candidates/${candidateId}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Lỗi khi tải hồ sơ ứng viên.');
            }

            const container = document.getElementById('structuredResults');
            renderStructuredProfile(container, data);
            
            aiProfileModal.classList.remove('hidden');
        } catch (error) {
            console.error("Lỗi khi mở hồ sơ:", error);
            alert(`Không thể tải hồ sơ: ${error.message}`);
        }
    };

    const closeAiProfileModal = () => {
        aiProfileModal.classList.add('hidden');
        document.getElementById('structuredResults').innerHTML = '';
    };

    closeProfileModalBtn.addEventListener('click', closeAiProfileModal);
    window.addEventListener('click', (event) => {
        if (event.target === aiProfileModal) {
            closeAiProfileModal();
        }
    });

    const renderStructuredProfile = (container, data) => {
        if (!data) {
            container.innerHTML = '<p class="no-data">Không có dữ liệu hồ sơ.</p>';
            return;
        }

        const { personal_info, summary, work_experience, education, skills, certifications, languages } = data.structured_data_json || {};
        const analysisResult = data.analysis_result_text;
        const references = data.references_json || []; // NEW: Get references data

        // --- SỬA LỖI URL ---
        const createAbsoluteUrl = (url) => {
            if (!url) return null;
            if (url.startsWith('http://') || url.startsWith('https://')) {
                return url;
            }
            return `https://${url}`;
        };

        const linkedInUrl = createAbsoluteUrl(personal_info?.linkedin_url);
        const portfolioUrl = createAbsoluteUrl(personal_info?.portfolio_url);
        // --- KẾT THÚC SỬA LỖI ---


        let htmlContent = `
            <h2>Hồ sơ của ứng viên: ${personal_info?.full_name || 'Chưa rõ'}</h2>
            <div class="result-box personal-info-box">
                <h3><span class="material-icons">person</span> Thông tin cá nhân</h3>
                <p class="name">${personal_info?.full_name || 'Chưa rõ tên'}</p>
                ${personal_info?.age ? `<p><span class="material-icons">calendar_today</span> Tuổi: ${personal_info.age}</p>` : ''}
                <div class="contact-info">
                    ${personal_info?.email ? `<p><span class="material-icons">email</span> ${personal_info.email}</p>` : ''}
                    ${personal_info?.phone_number ? `<p><span class="material-icons">phone</span> ${personal_info.phone_number}</p>` : ''}
                    ${personal_info?.address ? `<p><span class="material-icons">location_on</span> ${personal_info.address}</p>` : ''}
                    ${linkedInUrl ? `<p><span class="material-icons">link</span> <a href="${linkedInUrl}" target="_blank">LinkedIn</a></p>` : ''}
                    ${portfolioUrl ? `<p><span class="material-icons">link</span> <a href="${portfolioUrl}" target="_blank">Portfolio</a></p>` : ''}
                </div>
            </div>
        `;

        if (summary) {
            htmlContent += `
                <div class="result-box">
                    <h3><span class="material-icons">description</span> Tóm tắt</h3>
                    <p>${summary}</p>
                </div>
            `;
        }

        if (work_experience && work_experience.length > 0) {
            htmlContent += `
                <div class="result-box">
                    <h3><span class="material-icons">work</span> Kinh nghiệm làm việc</h3>
                    ${work_experience.map(exp => {
                        let title = exp.position || '';
                        if (title && exp.company_name) {
                            title += ` tại ${exp.company_name}`;
                        } else if (exp.company_name) {
                            title = exp.company_name;
                        }
                        
                        return `
                        <div class="data-card">
                            <div class="data-card-header">
                                <span class="title">${title}</span>
                                <span class="date">${exp.start_date || ''} - ${exp.end_date || 'Hiện tại'}</span>
                            </div>
                            ${exp.responsibilities && exp.responsibilities.length > 0 ? `
                                <ul class="responsibilities">
                                    ${exp.responsibilities.map(resp => `<li>${resp}</li>`).join('')}
                                </ul>
                            ` : ''}
                        </div>
                    `}).join('')}
                </div>
            `;
        }

        if (education && education.length > 0) {
            htmlContent += `
                <div class="result-box">
                    <h3><span class="material-icons">school</span> Học vấn</h3>
                    ${education.map(edu => {
                        const titleParts = [];
                        if (edu.degree) titleParts.push(edu.degree);
                        if (edu.major) titleParts.push(edu.major);
                        const title = titleParts.join(' - ');

                        return `
                        <div class="data-card">
                            <div class="data-card-header">
                                <span class="title">${title}</span>
                                <span class="date">${edu.graduation_year || ''}</span>
                            </div>
                            ${edu.institution_name ? `<p class="subtitle">${edu.institution_name}</p>` : ''}
                            ${edu.gpa ? `<p>GPA: ${edu.gpa}</p>` : ''}
                            ${edu.thesis_project ? `<p>Dự án/Luận văn: ${edu.thesis_project}</p>` : ''}
                        </div>
                    `}).join('')}
                </div>
            `;
        }

        if (skills && (skills.technical?.length > 0 || skills.soft?.length > 0)) {
            htmlContent += `
                <div class="result-box" id="skillsContainer">
                    <h3><span class="material-icons">build</span> Kỹ năng</h3>
                    ${skills.technical && skills.technical.length > 0 ? `
                        <div class="skill-category">
                            <h4>Kỹ năng chuyên môn</h4>
                            <div class="skills-list">
                                ${skills.technical.join(', ')}
                            </div>
                        </div>
                    ` : ''}
                    ${skills.soft && skills.soft.length > 0 ? `
                        <div class="skill-category">
                            <h4>Kỹ năng mềm</h4>
                            <div class="skills-list">
                                ${skills.soft.join(', ')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        }
        
        if (certifications && certifications.length > 0) {
            htmlContent += `
                <div class="result-box">
                    <h3><span class="material-icons">verified</span> Chứng chỉ</h3>
                    ${certifications.map(cert => `
                        <div class="data-card">
                            <div class="data-card-header">
                                <span class="title">${cert.name || ''}</span>
                                <span class="date">${cert.year || ''}</span>
                            </div>
                            ${cert.issuing_organization ? `<p class="subtitle">${cert.issuing_organization}</p>`: ''}
                        </div>
                    `).join('')}
                </div>
            `;
        }

        if (languages && languages.length > 0) {
            htmlContent += `
                <div class="result-box">
                    <h3><span class="material-icons">language</span> Ngôn ngữ</h3>
                    <div class="skills-list">
                        ${languages.map(lang => {
                            let langText = lang.language || '';
                            if (langText && lang.proficiency) {
                                langText += ` (${lang.proficiency})`;
                            }
                            return `${langText}`
                        }).join(', ')}
                    </div>
                </div>
            `;
        }
        
        // NEW: References section
        if (references && references.length > 0) {
            htmlContent += `
                <div class="result-box">
                    <h3><span class="material-icons">group</span> Người tham chiếu</h3>
                    ${references.map(ref => `
                        <div class="data-card">
                            <div class="data-card-header">
                                <span class="title">${ref.name || 'Chưa rõ tên'}</span>
                                ${ref.title ? `<span class="subtitle">${ref.title}</span>` : ''}
                            </div>
                            ${ref.company ? `<p>Công ty: ${ref.company}</p>` : ''}
                            ${ref.contact ? `<p>Liên hệ: ${ref.contact}</p>` : ''}
                        </div>
                    `).join('')}
                </div>
            `;
        }

        if (analysisResult) {
            let formattedContent = '';
            const analysisTitle = '[PHÂN TÍCH MỨC ĐỘ PHÙ HỢP VỚI JD]';
            const startIndex = analysisResult.indexOf(analysisTitle);

            if (startIndex !== -1) {
                const nextSectionIndex = analysisResult.indexOf('[', startIndex + 1);
                let rawContent = (nextSectionIndex !== -1)
                    ? analysisResult.substring(startIndex, nextSectionIndex)
                    : analysisResult.substring(startIndex);
                
                let processedContent = rawContent.replace(analysisTitle, '')
                                                 .replace(/\*\*/g, ' ')
                                                 .replace(/\*/g, '-');

                formattedContent = processedContent.split('\n')
                    .map(line => line.trim().replace(/\s\s+/g, ' '))
                    .filter(line => line.length > 0)
                    .join('\n');
            }

            if(formattedContent) {
                htmlContent += `
                    <div class="result-box">
                        <h3><span class="material-icons">analytics</span> Phân tích và Đánh giá</h3>
                        <pre>${formattedContent}</pre>
                    </div>
                `;
            }
        }

        container.innerHTML = htmlContent;
    };

    // Initial Load
    fetchAndRenderRecruiterJobs();
});