import time
import calendar
from flask import Flask, request, render_template, session, redirect
from instagram.client import InstagramAPI

app = Flask(__name__)
app.secret_key = 'Orion123'


# configure Instagram API
instaConfig = {
	'client_id': 'b168bdd5f96a4dc79f57414acba2afc6',
	'client_secret': 'b3d700d43d2a4461a3bc7d5a97f312a0',
	'redirect_uri': 'http://213.141.148.177:5000/instagram_callback'
}
api = InstagramAPI(**instaConfig)


# Overview page
@app.route('/')
def user_self():
	if 'instagram_access_token' in session and 'instagram_user' in session:
		user_api = InstagramAPI(access_token=session['instagram_access_token'])
		self_id = session['instagram_user'].get('id')
		self_user = user_api.user(user_id=self_id)
		# get 3 most popular fotos && likes count
		recent_media, _next_ = api.user_recent_media(access_token=session['instagram_access_token'], count=-1)
		max_liked_three_photos = {}
		for media in recent_media:
			if len(max_liked_three_photos) < 3:
				max_liked_three_photos.update({media.id: [media.like_count, media.get_low_resolution_url()]})
			else:
				min_key = min(max_liked_three_photos, key=max_liked_three_photos.get)
				if media.like_count > max_liked_three_photos[min_key][0]:
					del max_liked_three_photos[min_key]
					max_liked_three_photos.update({media.id: [media.like_count, media.get_low_resolution_url()]})
		return render_template("index.html",
									user=self_user,
									top_photos=max_liked_three_photos)
	else:
		return redirect('/connect')


# reports page
@app.route('/activities')
def show_activities():
	#show media posts by month
	d_time_media = {}
	set_time_media = set()
	all_media, next_url = api.user_recent_media(access_token=session['instagram_access_token'], count=15)
	while next_url:
		new_media, next_url = api.user_recent_media(access_token=session['instagram_access_token'], with_next_url=next_url, count=5)
		all_media.extend(new_media)
	for media in all_media:
		month_abbr = calendar.month_abbr[media.created_time.month]
		if month_abbr not in set_time_media:
			set_time_media.add(month_abbr)
			d_time_media.update({month_abbr: 1})
		else:
			d_time_media[month_abbr] += 1

	return render_template("activities.html",
	                       d_time_counts = d_time_media)


# Redirect users to Instagram for login
@app.route('/connect')
def main():
	url = api.get_authorize_url(scope=["likes", "comments"])
	return redirect(url)


# Instagram will redirect users back to this route after successfully logging in
@app.route('/instagram_callback')
def instagram_callback():
	code = request.args.get('code')

	if code:

		access_token, user = api.exchange_code_for_access_token(code)
		if not access_token:
			return 'Could not get access token'

		app.logger.debug('got an access token')
		app.logger.debug(access_token)

		# Sessions are used to keep this data 
		session['instagram_access_token'] = access_token
		session['instagram_user'] = user

		return redirect('/')  # redirect back to main page

	else:
		return "Uhoh no code provided"


@app.errorhandler(404)
def page_not_found(error):
	return render_template('404.html'), 404


# This is a jinja custom filter
@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
	py_date = time.strptime(date, '%a %b %d %H:%M:%S +0000 %Y')  # convert instagram date string into python date/time
	return time.strftime('%Y-%m-%d %h:%M:%S', py_date)  # return the formatted date.


if __name__ == "__main__":
	app.debug = True
	app.run(host='192.168.1.221', port=5000)
