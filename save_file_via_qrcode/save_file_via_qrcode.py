# -*- coding: utf-8 -*-
import os
import socket
from qrcode import QRCode
from flask import Flask, render_template, request
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class, ALL
from flask_wtf import FlaskForm, Form
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, FieldList

app = Flask(__name__)
app.config['SECRET_KEY'] = 'I have a dream'
upload_path = os.path.join(os.getcwd(), 'uploaddata')
if not os.path.exists(upload_path):
    os.mkdir(upload_path)
app.config['UPLOADED_DEFAULTS_DEST'] = upload_path

# photos = UploadSet('photos', IMAGES)
defaults_upload = UploadSet('DEFAULTS', ALL)

configure_uploads(app, defaults_upload)
patch_request_class(app)  # set maximum file size, default is 16MB


class UploadForm(FlaskForm):
    # file = FileField(validators=[
    #     FileAllowed(defaults_upload, u'类型无法上传'),
    #     FileRequired(u'文件未选择！')],
    #     )
    files = FieldList(FileField(FileAllowed(defaults_upload, u'类型无法上传')), 'attachment')
    submit = SubmitField(u'上传')


class ComposeForm(FlaskForm):
    attachment = FieldList(FileField('file'), 'attachment')
    add_upload = SubmitField(u'上传')


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    # form = UploadForm()
    form = ComposeForm()
    file_url = None
    for f in request.files.getlist('file'):
        print(f)
        filename = defaults_upload.save(f)
        file_url = defaults_upload.url(filename)

    return render_template('index.html', form=form, file_url=file_url)


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def generate_qrcode():
    q = QRCode()
    ip = get_host_ip()
    q.add_data('http://%s:5000' % ip)
    im = q.make_image()
    im.show()


if __name__ == '__main__':
    generate_qrcode()
    app.run(host='0.0.0.0', port=5000)
