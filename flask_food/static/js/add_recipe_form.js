

document.addEventListener('DOMContentLoaded', function () {
    const imageUploadInput = document.getElementById('imageUpload');
    const imagePreviewGrid = document.getElementById('imagePreviewGrid');
    const addImageButtonSlot = document.getElementById('addImageButton');
    const MAX_IMAGES = 9;
    let uploadedFiles = []; // 用于存储 File 对象

    console.log('addImageButtonSlot:', addImageButtonSlot);

    // 触发文件选择框3
    if (addImageButtonSlot) {
        addImageButtonSlot.addEventListener('click', () => {
            if (uploadedFiles.length < MAX_IMAGES) {
                imageUploadInput.click();
            } else {
                alert(`最多只能上传 ${MAX_IMAGES} 张图片。`);
            }
        });
    }else {
        console.error('addImageButtonSlot not found!');
    }

    // 处理文件选择
    if (imageUploadInput) {
        imageUploadInput.addEventListener('change', handleFiles);
    }

    function handleFiles(event) {
        const files = Array.from(event.target.files);
        const currentFileCount = uploadedFiles.length;
        const availableSlots = MAX_IMAGES - currentFileCount;

        if (files.length > availableSlots) {
            alert(`你还可以上传 ${availableSlots} 张图片，你选择了 ${files.length} 张。将只添加前 ${availableSlots} 张。`);
            files.splice(availableSlots); // 只取允许数量的文件
        }

        files.forEach(file => {
            if (!file.type.startsWith('image/')) {
                alert(`文件 "${file.name}" 不是图片格式，将被忽略。`);
                return;
            }
            if (uploadedFiles.length < MAX_IMAGES) {
                uploadedFiles.push(file); // 存储 File 对象
                createPreview(file, uploadedFiles.length - 1); // 传递索引
            }
        });
        // 清空 input 的值，以便下次可以再次选择相同文件
        event.target.value = null;
        updateAddButtonVisibility();
    }

    function createPreview(file, index) {
        const reader = new FileReader();
        reader.onload = function (e) {
            const previewSlot = document.createElement('div');
            previewSlot.classList.add('preview-slot');
            previewSlot.dataset.fileIndex = index; // 存储文件在 uploadedFiles 中的索引

            const img = document.createElement('img');
            img.src = e.target.result;
            previewSlot.appendChild(img);

            const deleteBtn = document.createElement('button');
            deleteBtn.classList.add('delete-image-btn');
            deleteBtn.innerHTML = '×'; // 'X' 符号
            deleteBtn.type = 'button'; // 防止触发表单提交
            deleteBtn.addEventListener('click', (event) => {
                event.stopPropagation(); // 防止点击事件冒泡到父元素(触发文件选择)

                // 从 uploadedFiles 数组中移除对应的 File 对象
                // 注意：直接删除 previewSlot.dataset.fileIndex 对应的元素可能会导致后续索引混乱
                // 更好的方式是标记为 null，然后在提交时过滤掉，或者重建数组
                const fileIndexToRemove = parseInt(previewSlot.dataset.fileIndex, 10);

                // 创建一个新的数组，不包含要删除的元素
                const newUploadedFiles = [];
                for(let i = 0; i < uploadedFiles.length; i++) {
                    if (i !== fileIndexToRemove) {
                        newUploadedFiles.push(uploadedFiles[i]);
                    }
                }
                uploadedFiles = newUploadedFiles;

                // 移除预览元素
                previewSlot.remove();

                // 更新其余预览元素的 data-file-index
                const remainingPreviewSlots = imagePreviewGrid.querySelectorAll('.preview-slot');
                remainingPreviewSlots.forEach((slot, newIdx) => {
                    slot.dataset.fileIndex = newIdx;
                });

                updateAddButtonVisibility();
            });
            previewSlot.appendChild(deleteBtn);

            // 将新的预览插槽添加到“添加图片”按钮之前
            imagePreviewGrid.insertBefore(previewSlot, addImageButtonSlot);
        };
        reader.readAsDataURL(file);
    }

    function updateAddButtonVisibility() {
        if (uploadedFiles.length >= MAX_IMAGES) {
            if (addImageButtonSlot) addImageButtonSlot.style.display = 'none';
        } else {
            if (addImageButtonSlot) addImageButtonSlot.style.display = 'flex'; // 或者 'block' 等
        }
    }

    // 表单提交时，将 uploadedFiles 中的文件附加到 FormData
    const recipeForm = document.getElementById('addRecipeForm');
    if (recipeForm) {
        recipeForm.addEventListener('submit', function(event) {
            const submitButton = recipeForm.querySelector('button[type="submit"]'); // 或者给按钮一个 ID
            let originalButtonText = '';
            if (submitButton) {
                originalButtonText = submitButton.innerHTML;
                submitButton.disabled = true;
                submitButton.innerHTML = '发布中...'; // 或者类似的加载提示
            }
            event.preventDefault(); // 阻止默认提交，我们手动构建 FormData

            const formData = new FormData(recipeForm); // 获取表单中的文本数据

            // 清除可能存在的旧的 recipe_images (因为 input type=file 的 name 也是 recipe_images)
            formData.delete('recipe_images');

            // 将JS管理的图片文件添加到 FormData
            uploadedFiles.forEach((file, index) => {
                formData.append('recipe_images', file, file.name); // name 很重要
            });

            console.log("FormData to be sent:");
            for (let pair of formData.entries()) {
                    console.log(pair[0] + ': ' + (pair[1] instanceof File ? pair[1].name : pair[1]));
            }

                const csrfTokenInput = recipeForm.querySelector('input[name="csrf_token"]'); // 查找名为 csrf_token 的 input
                let csrfToken = null;
                if (csrfTokenInput) {
                    csrfToken = csrfTokenInput.value;
                } else {
                    console.warn('CSRF token input not found in form!');
                    // 你可能需要一个备用方案，或者确保它总是在那里
                }

                const fetchOptions = {
                    method: 'POST',
                    body: formData,
                };

                const headers = {};
                if (csrfToken) {
                    headers['X-CSRFToken'] = csrfToken;
                }

            fetch(recipeForm.action, {
                    method: 'POST',
                    body: formData,
                    headers:headers
                })
                .then(response => {
                    if (!response.ok) {
                        // 如果服务器返回非2xx状态码，尝试解析为文本错误
                        return response.text().then(text => {
                            throw new Error(`服务器错误: ${response.status} - ${text || response.statusText}`);
                        });
                    }
                    const contentType = response.headers.get("content-type");
                    if (response.ok) {
                        if (response.redirected) {
                            window.location.href = response.url;
                            return Promise.reject('redirected'); // 使用 Promise.reject 来中断链，因为重定向已处理
                        }
                        // 只有当 content-type 明确是 application/json 时才尝试解析 JSON
                        if (contentType && contentType.includes("application/json")) {
                            return response.json();
                        } else {
                            // 如果不是 JSON，但响应是 OK，可以记录或尝试解析为文本
                            console.warn("Received OK response but not JSON:", response);
                            return response.text().then(text => {
                                // 如果需要，可以在这里检查文本内容，例如是否是成功的消息
                                // 或者直接认为这不是我们期望的 JSON 成功响应
                                // return { success: true, message: "操作可能已成功，但响应格式非预期JSON。" };
                                // 或者，如果期望后端总是返回 JSON，那么这里可以抛出错误
                                throw new Error('服务器成功响应，但格式不是 JSON。');
                            });
                        }
                    } else { // 处理 HTTP 错误状态 (4xx, 5xx)
                        // 尝试解析为JSON（如果后端在出错时返回JSON错误信息）
                        if (contentType && contentType.includes("application/json")) {
                            return response.json().then(errData => {
                                throw new Error(errData.message || errData.error || `服务器错误: ${response.status}`);
                            });
                        } else {
                            // 如果错误响应不是JSON，则获取文本内容作为错误信息
                            return response.text().then(text => {
                                // 尝试从HTML中提取有用的错误信息，或显示通用错误
                                console.error("Server error HTML response:", text); // 打印HTML内容到控制台
                                // 这里的 text 就是那个 "<!doctype..." HTML 字符串
                                // 你可以尝试更智能地解析它，或者直接显示一个通用错误
                                let friendlyMessage = `请求失败，状态码: ${response.status}.`;
                                if (text.toLowerCase().includes("traceback")) { // 简单判断是否是Flask的调试错误页
                                    friendlyMessage += " 服务器返回了详细的错误信息，请检查服务器日志。";
                                }
                                // 或者直接显示你现在的错误：
                                // throw new Error(`服务器返回了非JSON错误响应 (状态码: ${response.status})。内容: ${text.substring(0,100)}...`);
                                throw new Error(friendlyMessage);
                            });
                        }
                    }
                })
                .then(data => { // data 现在更可能是有效的 JSON 对象或者 undefined (如果是重定向)
                    if (data && data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else if (data && data.success) { // 确保data存在且有success标记
                        console.log('Success:', data.message || '操作成功完成！');
                        alert(data.message || '食谱发布成功！'); // 根据后端返回的 message 显示
                        // 如果没有 redirect_url，可能需要在这里做其他操作，比如清空表单
                    } else if (data) { // 如果data存在但没有明确的成功/重定向指令
                        console.warn('Received data from server with unclear instructions:', data);
                        form.reset(); // 例如，清空表单
                        document.getElementById('imagePreviewGrid').innerHTML = `
                            <div class="upload-slot add-image-button" id="addImageButton">
                                <i class="bi bi-plus-circle-dotted"></i>
                                <span>点击或拖拽添加图片</span>
                            </div>`; // 重置图片预览
                    } else {
                        alert('错误: ' + (data.message || '提交失败，请检查表单并重试。'));
                    }
                })
                 .catch(error => {
                    console.error('提交食谱时发生网络或解析错误:', error);
                    alert('提交过程中发生错误: ' + error.message);
                })
                .finally(() => {
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.innerHTML = originalButtonText;
                    }
                });
        });
    }

    // 初始化添加按钮状态
    updateAddButtonVisibility();
});