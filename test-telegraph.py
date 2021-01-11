import requests
from telegraph import Telegraph

telegraph = Telegraph()

telegraph.create_account(short_name='Барахолка')

# response = telegraph.create_page(title='Title',html_content='<p>Hello, world!</p>')
# response = telegraph.create_page(title='Title', content=[{"tag": "p", "children":["Hello,+world!"]}])

with open('business.jpg', 'rb') as f:
    with open('surf.jpg', 'rb') as g:
        paths = [x['src'] for x in requests.post('https://telegra.ph/upload', files={'1':('file', f, 'image/jpeg'),
                                                                '2':('file', g, 'image/jpeg')}).json()]
        print(paths)
with open('order_template.html', encoding='utf-8', mode='r') as template_file:
    template = template_file.read()
images_content = '\n'.join(["<img src = '{}' />".format(x) for x in paths])

html_content=template.format(images_content, 450, 'description')
# print(html_content)
response = telegraph.create_page('Title', html_content=html_content)
print(response)
print('https://telegra.ph/{}'.format(response['path']))
