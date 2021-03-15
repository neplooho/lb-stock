import requests
from telegraph import Telegraph
from requests_toolbelt.multipart.encoder import MultipartEncoder

telegraph = Telegraph()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest'
}
telegraph.create_account(short_name='Барахолка')

# response = telegraph.create_page(title='Title',html_content='<p>Hello, world!</p>')
# response = telegraph.create_page(title='Title', content=[{"tag": "p", "children":["Hello,+world!"]}])

with open('big.jpg', 'rb') as f:
    # with open('surf.jpg', 'rb') as g:
        # print(type(f))
        # print(type(g))
    print(f.readlines().__sizeof__())
    # print(f.__sizeof__())
    # multipart_data = MultipartEncoder(
    #     fields={
    #         # a file upload field
    #         'file': ('file.zip', f, 'image/jpeg')
    #         # plain text fields
    #         # 'field0': 'value0',
    #         # 'field1': 'value1',
    #     }
    # )
    # s = requests.session()
    # # content = s.post('https://telegra.ph/upload', files={'1':('file', f, 'image/jpeg')})
    # content = s.post('https://telegra.ph/upload', data=multipart_data, headers={'Content-Type':multipart_data.content_type})
    # print(content.json())
    # paths = [x['src'] for x in requests.post('https://telegra.ph/upload', files={'1':('file', f, 'image/jpeg')}).json()]
    # print(paths)
# with open('order_template.html', encoding='utf-8', mode='r') as template_file:
#     template = template_file.read()
# images_content = '\n'.join(["<img src = '{}' />".format(x) for x in paths])
#
# html_content=template.format(images_content, 450, 'description')
# print(html_content)
# response = telegraph.create_page('Title', html_content=html_content)
# print(response)
# print('https://telegra.ph/{}'.format(response['path']))
