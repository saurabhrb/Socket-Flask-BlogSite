from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading
from time import gmtime, strftime
import os
import atexit
import webbrowser
import pprint
import eventlet
import sys

from db import DATABASE

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

pp = pprint.PrettyPrinter(indent=1)
DB = DATABASE('DATABASE_FILE')
APP = Flask(__name__)
SOCKETIO = SocketIO(APP)

@APP.route('/')
def index():
    js_var = '/static/js/index.js' + '?' + strftime("%Y%m%d%H%M%S", gmtime())
    return render_template("index.html",js_var=js_var)

@APP.route('/save_and_quit')
def shut_off_save():
    SOCKETIO.emit('disconnect_it',broadcast=True,namespace='/socketio')
    close_server(1)
    return "CLOSED"

@APP.route('/quit_without_save')
def shut_off_nosave():
    SOCKETIO.emit('disconnect_it',broadcast=True,namespace='/socketio')
    close_server(0)
    return "CLOSED"

def close_server(save):
    if save:
        print('DB Saved')
        DB.show_db()
        DB.save_close()
    else:
        DB.show_db()
        print('DB not saved')
    eventlet.sleep(0.5)
    SOCKETIO.stop()
    SOCKETIO.shutdown()

@SOCKETIO.on('connect', namespace='/socketio')
def connect_socket():
    # print(str(request.sid) + ' connected')
    pass

@SOCKETIO.on('disconnect', namespace='/socketio')
def connect_socket2():
    DB.socket_disconnect(request.sid)
    DB.show_db()

@SOCKETIO.on('register_me',namespace='/socketio')
def reg_user(data):
    if DB.register_new(data):
        print('"' + data['user_'] + '" registered')
        emit('notif_card',{'succ':1,'data' : 'User registered'},namespace='/socketio')
        lst_html,usr_drop = DB.get_online_list()
        emit('users_list',lst_html,namespace='/socketio',broadcast=True)
        emit('user_drp',usr_drop,namespace='/socketio',broadcast=True)
    else:
        print('"' + data['user_'] + '" not registered. User already exists')
        emit('notif_card',{'succ':0,'data' : data['user_'] + ' already exists'},namespace='/socketio')
    DB.show_db()

@SOCKETIO.on('login_me',namespace='/socketio')
def log_user(data):
    res,msg  = DB.login_me(data,request.sid)
    print(msg)
    emit('notif_card',{'succ':res,'data':msg})
    if res:
        emit('logged_in',data['user_'])
        lst_html,usr_drop = DB.get_online_list()
        emit('users_list',lst_html,namespace='/socketio',broadcast=True)
        emit('user_drp',usr_drop,namespace='/socketio',broadcast=True)
        notif_lst = DB.get_notifs(data['user_'])
        if len(notif_lst) > 0:
            notif_htm = ''
            for mess in notif_lst:
                pp.pprint(mess)
                id_ = mess['id']
                src = mess['src']
                dst = mess['dst']
                time_ = mess['time']
                if src == data['user_']:
                    src = 'YOU'
                if dst == data['user_']:
                    dst = 'YOU'
                notif_htm = '<li onlick=\"scroll_to_me(\'mess_'+ str(id_) + '\')\"><a href="#mess_'+ str(id_) +'" onlick=\"scroll_to_me(\'mess_'+ str(id_) + '\')\">'+ src +' ► '+ dst + '    <p style="font-size:10px;color:#80808080">'+time_+'</p></a></li>' + notif_htm
            emit('notifs',{'htm' : notif_htm,'cnts' : len(notif_lst)},namespace='/socketio')
        mess_htm = DB.get_all_msgs_HTML(data['user_'])
        emit('all_mess',mess_htm,namespace='/socketio')
    DB.show_db()


@SOCKETIO.on('get_user_details',namespace='/socketio')
def get_det(username):
    det = DB.get_usr_details(username)
    htm = ''
    for k in det.keys():
        if k != 'pass':
            htm+= str(k) + ' : ' + str(det[k]) + '<br>'
    pp.pprint(det)
    emit('get_user_details',htm,namespace='/socketio')

@SOCKETIO.on('get_my_details',namespace='/socketio')
def get_my_details(username):
    det = DB.get_usr_details(username)
    htm = ''
    for k in det.keys():
        if k != 'pass':
            htm+= str(k) + ' : ' + str(det[k]) + '<br>'
    pp.pprint(det)
    emit('get_my_details',htm,namespace='/socketio')


@SOCKETIO.on('logged_out',namespace='/socketio')
def logged_out(username):
    DB.log_out(username)
    lst_html,usr_drop = DB.get_online_list()
    emit('users_list',lst_html,namespace='/socketio',broadcast=True)
    emit('user_drp',usr_drop,namespace='/socketio',broadcast=True)
    DB.show_db()

@SOCKETIO.on('send_message',namespace='/socketio')
def send_mess(data):
    msg = data['msg']
    src = data['src']
    dst = data['dst']
    mess = {}
    mess['src'] = src
    mess['dst'] = dst
    mess['msg'] = msg
    time_ = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    mess['time'] = time_
    mess_id = DB.new_message(mess)
    emit('send_message',{'src':src,'dst':dst,'msg':msg,'time':time_,'id':mess_id},namespace='/socketio',broadcast=True)
    DB.show_db()

def exit_handler():
    print("SERVER CLOSED!")

atexit.register(exit_handler)

if __name__ == '__main__':
    print('')
    browse_url = 'http://localhost:'+str(5000)+'/'
    threading.Timer(1.25, lambda: webbrowser.open(browse_url) ).start()
    SOCKETIO.run(APP,port=5000)
