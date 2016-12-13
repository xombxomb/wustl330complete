from flask import Flask, request, redirect, render_template
import twilio.twiml
from forms import MessageForm
from twilio.rest import TwilioRestClient
import urllib
import os, random
import json
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import base64
import pprint

account_sid = "AC4d88e8c90d9a0e0d1756e53ce60cc0fd"
auth_token = "0d313fa30fd754358dea3b06dc365ebc"
client = TwilioRestClient(account_sid, auth_token)

app = Flask(__name__)
app.config.from_object('config')

def doggit_vision_verify(photo_file_path):
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build('vision', 'v1', credentials=credentials)

    with open(photo_file_path, 'rb') as image:
        image_content = base64.b64encode(image.read())
        service_request = service.images().annotate(body={
            'requests': [{
                'image': {
                    'content': image_content.decode('UTF-8')
                },
                'features': [{
                    'type': 'LABEL_DETECTION',
                    'maxResults': 3
                }]
            }]
        })
        response = service_request.execute()
        label = response['responses'][0]['labelAnnotations']
        return label


@app.route("/", methods=['GET', 'POST'])
def process_image():
    

    mediaURl = request.values.get('MediaUrl0', None)
    content_type = request.values.get('MediaContentType0', None)
    message_body = request.values.get('Body', None)
    
    if (mediaURl == None):
        resp = twilio.twiml.Response()
        resp.message("You've reached Doggit, but it looks like you forgot your image!")
        return str(resp)
        
    if (content_type != "image/jpeg" and content_type != "image/png"):
        resp = twilio.twiml.Response()
        resp.message("Sorry, we only accept jpegs and pngs currently")
        return str(resp)

    if (message_body == "" or message_body == None):
        message_body = "Dog!"

    
    print(request.values.get('From', None))
    print(request.values.get('MediaUrl0', None))
    print(request.values.get('MediaContentType0', None))
    file_type = content_type.replace("image/", "")
    if (file_type == "jpeg"):
        file_type = "jpg"
    print(file_type)
    raw_file_name = mediaURl.rsplit('/', 1)[-1]
    typed_file_name = raw_file_name + "." + file_type
    print(raw_file_name)
    myPath = "static/imgs/"
    full_file_name = os.path.join(myPath, typed_file_name)
    os.system('wget %s' % mediaURl)
    os.system('mv %s %s' % (raw_file_name, full_file_name))
    label = doggit_vision_verify(full_file_name)
    print("**********")
    pprint.pprint(label)
    print("**********")
    if (label[0]['description'] != "dog" and label[1]['description'] != "dog" and label[2]['description'] != "dog" ):
        os.system('rm %s' % full_file_name)
        resp = twilio.twiml.Response()
        resp.message("DoggitVision failed to ID a dog in your photo. Your photo was identifed as: " + label[0]['description']
                     + ", " + label[1]['description'] + ", " + label[2]['description'])
        return str(resp)
    img_data = {
        'photoID': raw_file_name,
        'static_link': full_file_name,
        'comment': message_body
    }
    jsonPath ="static/json_data/"
    full_json_name = raw_file_name + ".json"
    full_json_name = os.path.join(jsonPath, full_json_name)
    with open(full_json_name, 'w') as f:
        json.dump(img_data, f)

    
    ##message_id = request.values.get('Body', None)
    ##message_obj = client.messages.get(message_id)
    ##message_obj.media_list.delete()
    resp = twilio.twiml.Response()
    resp.message("Thanks! your image has been recieved. Your image's DoggitID is: " + raw_file_name)
    return str(resp)


@app.route("/index", methods=['GET', 'POST'])
def index():
    form = MessageForm()
    image_sources = os.listdir('static/json_data/')
    image_sources = ['static/json_data/' + x for x in image_sources]
    image_data = []
    for json_file in image_sources:
        with open(json_file) as json_:
            data = json.load(json_)
            print(data['static_link'])
            image_data.append(data)
        
    random.shuffle(image_data)
    if form.validate_on_submit():
        contact = form.number.data
        blurb = "Welcome to Doggit! Please send pictures to this number for submission. You may optionally include a caption!"
        print(contact)
        print("click")
        message = client.messages.create(to=contact, from_="+13143100209",
                                         body=blurb)
        return redirect('/index')


    return render_template('index.html',
                           form=form,
                           image_sources=image_data)

@app.route("/view", methods=['GET', 'POST'])
def viewPhoto():
    photoID = request.args.get('photoid')
    form = MessageForm()
    photojson = "static/json_data/" + photoID + ".json"
    with open(photojson) as json_:
        photo_data = json.load(json_)
    
    if form.validate_on_submit():
        contact = form.number.data
        mediaurl = form.media.data
        print(contact)
        print(mediaurl)
        message = client.messages.create(to=contact, from_="+13143100209",
                                         body="Heres your pic!", media_url=[mediaurl])
        return redirect('/index')

    return render_template('view.html',
                           photo=photo_data,
                           form=form)

@app.route("/random", methods=['GET', 'POST'])
def showRandom():
    image_sources = os.listdir('static/json_data/')
    image_sources = ['static/json_data/' + x for x in image_sources]
    image_data = []
    for json_file in image_sources:
        with open(json_file) as json_:
            data = json.load(json_)
            print(data['static_link'])
            image_data.append(data)
    
    random.shuffle(image_data)
    image = image_data[1]
    return render_template('random.html', image=image)
if __name__ == "__main__":
    app.run(debug=True)
