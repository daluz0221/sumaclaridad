import uuid
from io import BytesIO

import boto3
from django.conf import settings
from django.utils import timezone
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


def is_s3_pdf_key(value):
    if not value or value.startswith('pending://'):
        return False
    return True


def s3_client():
    kwargs = {'region_name': settings.AWS_S3_REGION}
    if settings.AWS_ACCESS_KEY_ID:
        kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
        kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
    return boto3.client('s3', **kwargs)


def fetch_base_pdf(key):
    response = s3_client().get_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
    return response['Body'].read()


def watermark_pdf(source_bytes, name, email, when=None):

    when = when or timezone.localtime()
    stamp = f'{name} · {email} · {when.strftime("%Y-%m-%d")}'

    reader = PdfReader(BytesIO(source_bytes))
    writer = PdfWriter()

    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        overlay_buf = BytesIO()
        c = canvas.Canvas(overlay_buf, pagesize=(width, height))
        c.setFillColorRGB(0.45, 0.45, 0.45)
        c.setFillAlpha(0.28)
        c.setFont('Helvetica', 9)
        c.drawString(18, 16, stamp)
        c.save()
        overlay_buf.seek(0)
        overlay = PdfReader(overlay_buf)
        page.merge_page(overlay.pages[0])
        writer.add_page(page)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()


def store_watermarked_pdf(pdf_bytes, user_id, resource_id):
    key = f'tmp/watermarked/{user_id}/{resource_id}/{uuid.uuid4().hex}.pdf'
    s3_client().put_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=key,
        Body=pdf_bytes,
        ContentType='application/pdf',
        ServerSideEncryption='AES256',
    )

    return key


def presigned_download_url(key, filename):
    return s3_client().generate_presigned_url(
        'get_object',
        Params={
            'Bucket': settings.AWS_S3_BUCKET,
            'Key': key,
            'ResponseContentDisposition': f'attachment; filename="{filename}"',
        },
        ExpiresIn=settings.AWS_S3_SIGNED_URL_TTL,
    )


def issue_watermarked_download(base_key, user, resource_id, filename):
    raw = fetch_base_pdf(base_key)
    marked = watermark_pdf(raw, user.name, user.email)
    marked_key = store_watermarked_pdf(marked, user.id, resource_id)
    return presigned_download_url(marked_key, filename)

