// Agrega esto en tus archivos estáticos, por ejemplo en static/js/ckeditor-config.js
class MyUploadAdapter {
    constructor(loader) {
        this.loader = loader;
    }
    upload() {
        return this.loader.file
            .then(file => new Promise((resolve, reject) => {
                const data = new FormData();
                data.append('upload', file);
                fetch('/upload_image/', {
                    method: 'POST',
                    body: data,
                })
                .then(response => response.json())
                .then(result => resolve({ default: result.url }))
                .catch(error => reject(error));
            }));
    }
}
function MyCustomUploadAdapterPlugin(editor) {
    editor.plugins.get('FileRepository').createUploadAdapter = (loader) => {
        return new MyUploadAdapter(loader);
    };
}
ClassicEditor
    .create(document.querySelector('.editor'), {
        extraPlugins: [MyCustomUploadAdapterPlugin],
    })
    .catch(error => console.error(error));
