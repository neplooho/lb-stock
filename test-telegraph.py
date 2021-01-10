import requests
from telegraph import Telegraph

telegraph = Telegraph()

telegraph.create_account(short_name='Барахолка')

# response = telegraph.create_page(title='Title',html_content='<p>Hello, world!</p>')
# response = telegraph.create_page(title='Title', content=[{"tag": "p", "children":["Hello,+world!"]}])

with open('business.jpg', 'rb') as f:
    with open('surf.jpg', 'rb') as g:
        paths = [x['src'] for x in requests.post('https://telegra.ph/upload', files={'fileone':('file', f, 'image/jpeg'),
                                                                'filetwo':('file', g, 'image/jpeg')}).json()]
        print(paths)

response = telegraph.create_page('Hey', html_content="<p>Hello, world!</p>\n<img src='{}'/>\n<img src='{}'/>".format(paths[0], paths[1]))
print(response)
print('https://telegra.ph/{}'.format(response['path']))
