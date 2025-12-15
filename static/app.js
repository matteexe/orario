document.addEventListener('DOMContentLoaded', function() {
    const tutteCheckbox = document.getElementById('tutte');
    const classiCheckboxes = document.querySelectorAll('input[name="classi"]');
    const classiBox = document.querySelector('.classi-box');
    const form = document.querySelector('form');

    // Funzione per disabilitare/abilitare le classi individuali
    function toggleClassiIndividuali(disabled) {
        classiCheckboxes.forEach(cb => {
            cb.disabled = disabled;
            if (disabled) {
                cb.checked = false;
            }
        });

        if (classiBox) {
            if (disabled) {
                classiBox.classList.add('disabled');
            } else {
                classiBox.classList.remove('disabled');
            }
        }
    }

    // Gestione checkbox "Tutte le classi"
    if (tutteCheckbox) {
        // All'avvio, se "tutte" è checked, disabilita le altre
        if (tutteCheckbox.checked) {
            toggleClassiIndividuali(true);
        }

        tutteCheckbox.addEventListener('change', function() {
            if (this.checked) {
                // Deseleziona tutte le classi individuali quando si seleziona "Tutte"
                classiCheckboxes.forEach(cb => {
                    cb.checked = false;
                });
            }
            toggleClassiIndividuali(this.checked);
        });
    }

    // Gestione checkbox classi individuali
    classiCheckboxes.forEach(cb => {
        cb.addEventListener('change', function() {
            // Se almeno una classe individuale è selezionata, disabilita e deseleziona "tutte"
            const almenoUnaSelezionata = Array.from(classiCheckboxes).some(checkbox => checkbox.checked);

            if (tutteCheckbox) {
                if (almenoUnaSelezionata) {
                    tutteCheckbox.disabled = true;
                    tutteCheckbox.checked = false;
                } else {
                    tutteCheckbox.disabled = false;
                }
            }
        });
    });

    // Mostra loading durante il submit
    if (form) {
        form.addEventListener('submit', function(e) {
            const loading = document.getElementById('loading');
            const submitButton = form.querySelector('button[type="submit"]');

            if (loading) {
                loading.classList.add('active');

                // Disabilita il bottone durante il caricamento
                if (submitButton) {
                    submitButton.disabled = true;
                }

                // Nasconde il loading dopo 2 secondi (tempo per il download)
                setTimeout(function() {
                    loading.classList.remove('active');
                    if (submitButton) {
                        submitButton.disabled = false;
                    }
                }, 20000);

                // Backup: rimuove il loading se la pagina rimane attiva dopo 5 secondi
                setTimeout(function() {
                    if (loading.classList.contains('active')) {
                        loading.classList.remove('active');
                        if (submitButton) {
                            submitButton.disabled = false;
                        }
                    }
                }, 5000);
            }
        });
    }

    // Gestione drag and drop per file input
    const fileInput = document.querySelector('input[type="file"]');
    const uploadArea = document.getElementById('uploadArea');

    if (fileInput && uploadArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, function() {
                uploadArea.classList.add('drag-over');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, function() {
                uploadArea.classList.remove('drag-over');
            }, false);
        });

        uploadArea.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            const files = dt.files;

            if (files.length > 0) {
                fileInput.files = files;
                updateUploadText(files[0].name);
            }
        });

        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                updateUploadText(e.target.files[0].name);
            }
        });

        function updateUploadText(filename) {
            const uploadText = uploadArea.querySelector('.upload-text strong');
            if (uploadText) {
                uploadText.textContent = `✓ ${filename}`;
                uploadText.style.color = 'var(--success)';
            }
        }
    }
});
