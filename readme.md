This is real time parking management website implementing CRUD operations.
The application is built using Flask framework(Python) and Sql database.
The data is generated using the Faker Module of Python.
Background Scheduler checks the entry every 5 minutes and deletes it if the timeFrame is expired.
Role Based Authorization is implemented in this application using session.
It uses Password hashing method for authentication.
In the frontend part I have used HTML, Bootstrap and CSS.
<h4>To setup this on your local system. Follow the steps: </h4>
<p>To start with you need to setup a virtual environment. You can do it by following steps: </p>
<pre><code>python3 -m venv .venv
source venv/bin/activate</code></pre>
<p>After activating the virtualing environment, install the requirements<p>
<code>pip install -r requirements.txt</code>
<p>Now you can run the application</p>
<code>python app.py</code> 
