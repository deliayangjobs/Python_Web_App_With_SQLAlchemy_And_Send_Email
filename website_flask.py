from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from send_email import send_email
from sqlalchemy.sql import func

#when executing the script, __name__ will be __main__
#when import the script, __name__ will be the file name
app=Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:postgres1@localhost/height_collector'
app.config['SQLALCHEMY_DATABASE_URI']='postgres://kyvohrijdpuwko:eLRyyWkWJlwWHwR1zm_BNKL381@ec2-184-73-199-29.compute-1.amazonaws.com:5432/d2i8ho6bttqt7l?sslmode=require'
db=SQLAlchemy(app)

class Data(db.Model):
    __tablename__="data"
    id=db.Column(db.Integer, primary_key=True)
    email_=db.Column(db.String(120), unique=True)
    height_=db.Column(db.Integer)

    def __init__(self, email_, height_):
        self.email_=email_
        self.height_=height_


@app.route('/plot/')
def plot():
    from pandas_datareader import data
    import datetime
    from bokeh.plotting import figure, show, output_file
    from bokeh.embed import components
    from bokeh.resources import CDN

    start=datetime.datetime(2016,8,1)
    end=datetime.datetime(2016,11,1)
    df=data.DataReader(name="GOOG", data_source="google", start=start, end=end)

    p=figure(x_axis_type='datetime',width=1000,height=300,responsive=True)
    p.title="Candlestick Chart"
    p.grid.grid_line_alpha=0.3

    p.segment(df.index, df.High, df.index, df.Low, color="Black")

    hour_12=12*60*60*1000
    def inc_dec(c, o):
        if c > o:
            return "Increase"
        if c < o:
            return "Decrease"
        return "Equal"

    df["Status"]=[inc_dec(c,o) for c, o in zip(df.Close, df.Open)]
    df["Middle"]=(df.Open+df.Close)/2
    df["Height"]=abs(df.Open-df.Close)

    p.rect(df.index[df.Status=="Increase"], df.Middle[df.Status=="Increase"], hour_12,
        df.Height[df.Status=="Increase"], fill_color="#CCFFFF", line_color="black")

    p.rect(df.index[df.Status=="Decrease"], df.Middle[df.Status=="Decrease"], hour_12,
        df.Height[df.Status=="Decrease"], fill_color="#FF3333", line_color="black")

    script1, div1 = components(p)    #this is a turple with JS code and HTML code
    cdn_js=CDN.js_files[0]
    cdn_css=CDN.css_files[0]
    return render_template("plot.html", script1=script1, div1=div1, cdn_js=cdn_js, cdn_css=cdn_css)

@app.route('/')    #see http://localhost:5000/  #'/about/' see http://localhost:5000/about/
def home():
    return render_template("home.html")

@app.route('/about/')
def about():
    return render_template("about.html")

@app.route('/height')
def height():
    return render_template("index.html")

@app.route('/success', methods=['POST'])
def success():
    if request.method=='POST':
        email=request.form["email_name"]
        height=request.form["height_name"]

        if db.session.query(Data).filter(Data.email_==email).count() == 0:
            data=Data(email, height)
            db.session.add(data)
            db.session.commit()
            average_height=db.session.query(func.avg(Data.height_)).scalar()    #scalar is number, query is select str
            average_height=round(average_height,1)
            count=db.session.query(Data.height_).count()
            #send_email(email, height,average_height,count)
            return render_template("success.html")
        return render_template("index.html", text="Seems like we've got something from that email address already!")

if __name__=="__main__":
    app.run(debug=True)
