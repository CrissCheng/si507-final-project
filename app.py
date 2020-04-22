# coding=utf8
from flask import Flask, render_template, request
import sqlite3
import plotly.graph_objects as go
import plotly.express as px

app = Flask(__name__)

def connect_db(q):
	conn = sqlite3.connect('country_song.sqlite')
	cur = conn.cursor()
	results = cur.execute(q).fetchall()
	conn.close()

	return results

def get_countries():

	q = f'''
		SELECT c.countries
		FROM Countries as c
	'''
	results = connect_db(q)
	
	return results

def get_top_songs(country):
	q = f'''
		SELECT c.countries, v.id, v.title, v.artist_Name, v.album, v.url
		FROM Countries as c
		JOIN Videos as v
		ON v.CountryId = c.Id
		WHERE c.Countries = '{country}'
	'''
	results = connect_db(q)
	return results

def get_lyrics(song_id):

	q = f'''
		SELECT v.id, v.title, v.lyrics, v.embed_url
		FROM Videos as v
		WHERE id = '{song_id}'
		'''
	results = connect_db(q)
	return results	

def get_multiple_songs_stats(id_list, check_view = False, check_like = False, check_dislike = False, check_comment = False):
	q_select = 	f'''SELECT v.id, v.title'''
	if (check_view):
		q_select += "," + "v.views"
	if (check_like):
		q_select += "," + "v.likes"
	if (check_dislike):
		q_select += "," + "v.dislikes"
	if (check_comment):
		q_select += "," + "v.comment_count"

	q_rest = f'''
		FROM Videos as v
		WHERE id IN {id_list}
		'''
	q_rest = q_rest.replace('[', '(')
	q_rest = q_rest.replace(']', ')')
	q = q_select + q_rest
	results = connect_db(q)
	return results

def get_song_view(id_list):
	q = f'''
		SELECT v.id, v.title, v.views
		FROM Videos as v
		WHERE id IN {id_list}
		'''
	q = q.replace('[', '(')
	q = q.replace(']', ')')

	results = connect_db(q)
	return results
def get_song_like(id_list):
	q = f'''
		SELECT v.id, v.title, v.likes
		FROM Videos as v
		WHERE id IN {id_list}
		'''
	q = q.replace('[', '(')
	q = q.replace(']', ')')
	results = connect_db(q)
	return results

def get_song_dislike(id_list):
	q = f'''
		SELECT v.id, v.title, v.dislikes
		FROM Videos as v
		WHERE id IN {id_list}
		'''
	q = q.replace('[', '(')
	q = q.replace(']', ')')
	results = connect_db(q)
	return results
def get_song_comment(id_list):
	q = f'''
		SELECT v.id, v.title, v.comment_count
		FROM Videos as v
		WHERE id IN {id_list}
		'''
	q = q.replace('[', '(')
	q = q.replace(']', ')')
	results = connect_db(q)
	return results

def country_like_dislike():
	q = f'''
	SELECT v.id, c.Countries, v.likes, v.dislikes
	FROM Videos as v
	JOIN Countries as c
	ON v.countryId = c.id
	'''
	results = connect_db(q)
	return results
def top_views():
	q = f'''
	SELECT DISTINCT v.title, v.views
	FROM Videos as v
	JOIN Countries as c
	ON v.countryId = c.id
	ORDER BY views DESC
	LIMIT 10
	'''
	results = connect_db(q)
	return results


def like_dislike_comment():
	q = f'''
	SELECT v.id, c.Countries, v.likes, v.dislikes, v.comment_count
	FROM Videos as v
	JOIN Countries as c
	ON v.countryId = c.id
	'''
	results = connect_db(q)
	return results

@app.route('/')
def index():
	### get list of countries
	results = get_countries()
	country_list = []
	for i in results:
		country_list.append(i[0])
	country_list = list(dict.fromkeys(country_list))

	### populating lists in html
	return render_template('index.html', countries=country_list)

@app.route('/top_songs/<country>')
def top_songs(country):
	top_song_list = get_top_songs(country)
	return render_template('top_song.html', country=country, top_song_list=top_song_list)

@app.route('/top_songs/<country>/compare')
def top_congs_compare(country):
	top_song_list = get_top_songs(country)
	return render_template('top_songs_compare.html', country=country, top_song_list=top_song_list)

@app.route('/single_song/<country>/<song_id>/lyric')
def single_song_lyric(country, song_id):
	single_song = get_lyrics(int(song_id))
	return render_template('single_song_lyric.html',song_name=single_song[0][1],lyric=single_song[0][2], embed_url=single_song[0][3], country=country)

@app.route('/top_songs/<country>/results', methods=['POST'])
def song_compare_handle_form(country):
	top_song_list = get_top_songs(country)
	origina_country_song_id_list =[]

	# get all the song ids in the country
	for i in top_song_list:
		origina_country_song_id_list.append(i[1])

	# check if the song is checked in the form
	check_song_list = {}
	for i in origina_country_song_id_list:
		check_song_list[i]= str(i) in request.form.keys()

	# getting only the song ids that are checked in the form
	checked_song_true_list = []
	for i, v in check_song_list.items():
		if v == True:
			checked_song_true_list.append(i)

	check_view = "view" in request.form.keys()
	check_like = "like" in request.form.keys()
	check_dislike = "dislike" in request.form.keys()
	check_comment = "comment" in request.form.keys()
	songs_stats=get_multiple_songs_stats(checked_song_true_list,check_view,check_like,check_dislike,check_comment)
	checked_var_dict = {}
	if (check_view):
		view = get_song_view(checked_song_true_list)
	if (check_like):
		like = get_song_like(checked_song_true_list)
	if (check_dislike):
		dislike = get_song_dislike(checked_song_true_list)
	if (check_comment):
		comment = get_song_comment(checked_song_true_list)

	plot_results = request.form.get('plot', False)

	if (plot_results):
		if (check_view):
			x_vals = [i[1] for i in songs_stats]
			y_vals = [i[2] for i in view]
			bars_data = go.Bar(
				x=x_vals,
				y=y_vals
			)
			basic_layout = go.Layout(title = "View Counts for Different Songs")
			fig_1 = go.Figure(data=bars_data, layout=basic_layout)
			div_1 = fig_1.to_html(full_html=False)
		else:
			div_1 = ""
		if (check_like):
			x_vals = [i[1] for i in songs_stats]
			y_vals = [i[2] for i in like]
			bars_data = go.Bar(
				x=x_vals,
				y=y_vals
			)
			basic_layout = go.Layout(title = "Like Counts for Different Songs")

			fig_2 = go.Figure(data=bars_data, layout=basic_layout)
			div_2 = fig_2.to_html(full_html=False)
		else:
			div_2 = ""
		if (check_dislike):
			x_vals = [i[1] for i in songs_stats]
			y_vals = [i[2] for i in dislike]
			bars_data = go.Bar(
				x=x_vals,
				y=y_vals
			)
			basic_layout = go.Layout(title = "Dislike Counts for Different Songs")

			fig_3 = go.Figure(data=bars_data, layout=basic_layout)
			div_3 = fig_3.to_html(full_html=False)
		else:
			div_3 = ""
		if (check_comment):
			x_vals = [i[1] for i in songs_stats]
			y_vals = [i[2] for i in comment]
			bars_data = go.Bar(
				x=x_vals,
				y=y_vals
			)
			basic_layout = go.Layout(title = "Comment Counts for Different Songs")
			fig_4 = go.Figure(data=bars_data, layout=basic_layout)
			div_4 = fig_4.to_html(full_html=False)
		else:
			div_4 = ""
		return render_template('top_songs_compare_results_plot.html', country=country, plot_div_1 = div_1, plot_div_2 = div_2, plot_div_3 = div_3, plot_div_4 = div_4)
	else:
		return render_template('top_songs_compare_results.html', country=country, song_stats=songs_stats ,check_view = check_view, check_like = check_like, check_dislike = check_dislike, check_comment = check_comment)

@app.route('/like_dislike_compare')
def like_dislike_comp():
	results = country_like_dislike()
	like_list = []
	dislike_list = []
	country_list = []
	for i in results:
		country_list.append(i[1])
		like_list.append(i[2])
		dislike_list.append(i[3])
	
	fig = px.scatter(x=like_list, y=dislike_list, color=country_list, title = "like vs dislike counts across different countries", marginal_y="histogram", marginal_x="histogram")
	fig.update_layout(
		height =800
		)
	div = fig.to_html(full_html=False)
	return render_template('like_dislike_comp.html', plot_div = div)

@app.route('/like_dislike_comment_compare')
def like_dislike_comment_comp():
	results = like_dislike_comment()
	like_list = []
	dislike_list = []
	comment_list = []
	country_list = []
	for i in results:
		country_list.append(i[1])
		like_list.append(i[2])
		dislike_list.append(i[3])
		comment_list.append(i[4])
	
	fig = px.scatter_3d(x=like_list, y=dislike_list, z=comment_list, color=country_list, title = "like, dislike and comment counts across different countries")
	fig.update_layout(scene=dict(
		xaxis_title="like",
		yaxis_title="dislike",
		zaxis_title="comment"),
		height = 800
		)
	div = fig.to_html(full_html=False)
	return render_template('like_dislike_comment_comp.html', plot_div = div)

@app.route('/view_compare')
def view_comp():
	results = top_views()
	title = []
	view = []
	
	for i in results:
		title.append(i[0])
		view.append(i[1])
	print(view)
	fig = px.bar(x=title, y=view)
	div = fig.to_html(full_html=False)
	return render_template('views_compare.html', plot_div = div, title = "Top 10 viewed songs in the globe")


if __name__ == '__main__':
	app.run(debug=True)
	