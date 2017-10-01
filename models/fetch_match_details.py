from flask import Flask,render_template
import psycopg2

app = Flask(__name__)


def get_connection():
    try:
        conn = psycopg2.connect("dbname='dpl' user='ashraya' host='localhost' password='ashraya'")
        return conn
    except:
        print "I am unable to connect to the database"

def get_match_details(match_id):
    cur = get_connection().cursor()
    cur.execute("select dp.name as bet_by, db.amount,db.amount_won,(select name from dpl_participants where id=dm.participant_1),"
                "(select name from dpl_participants where id=dm.participant_2),(select name as winner from dpl_participants where id=dm.winner),(select name from dpl_participants where id=db.bet_on)   "
" from dpl_betting db, dpl_participants dp, dpl_match dm where db.name = dp.id and db.match =  dm.id and dm.id = %s order by dm.create_date desc"%match_id)
    return cur.fetchall()

def get_matches():
    cur = get_connection().cursor()
    cur.execute("select dm.id from dpl_match dm")
    return cur.fetchall()

@app.route("/details")
def get_details():
    matches = get_matches()
    final_details =""
    for match_row in matches:
        for match_id in match_row:
            details = get_match_details(match_id)
            if details:
                final_details +="<h3 align='center' >Match %s </h3>"%match_id
                final_details += "<table align='center'><th>Bet by</th><th>Bet Amount</th><th>Amount Won</th><th>Participant 1</th><th>Participant 2</th><th>Winner</th><th>Bet On</th>"
                for each_row in details:
                    final_details += "<tr>"
                    for each_column in each_row:
                        final_details += "<td>"+str(each_column)+"</td>"
                    final_details += "</tr>"
            final_details += "</table>"
    return render_template('details.html',details=final_details)

if __name__ == '__main__':
    app.run(debug=True,host='192.168.1.3')
