import os
import pprint
import pickle
from time import gmtime, strftime

pp = pprint.PrettyPrinter(indent=1)

class DATABASE:
	USERS = {}
	MESSAGES = {}
	NOTIFS = {}
	user_id = 0
	mess_id = 0
	
	def __init__(self,db_file_name):
		self.db_file = db_file_name
		if os.path.isfile(self.db_file):
			infile = open(self.db_file,'rb')
			dict_ = pickle.load(infile)
			infile.close()
			print('DATABASE loaded from pickle')
			pp.pprint(dict_)
			self.USERS = dict_['USERS']
			self.MESSAGES = dict_['MESSAGES']
			self.NOTIFS = dict_['NOTIFS']
			self.user_id = dict_['user_id']
			self.mess_id = dict_['mess_id']

	def update_before_close(self):
		for ids in self.USERS.keys():
			self.USERS[ids]['logged_in'] = 0
			self.USERS[ids]['session_id'] = ''

	def socket_disconnect(self,sid):
		for ids in self.USERS.keys():
			if self.USERS[ids]['session_id'] == sid:
				print(self.USERS[ids]['username'] + ' disconnected')
				self.USERS[ids]['logged_in'] = 0
				self.USERS[ids]['session_id'] = ''
				break

	def register_new(self,data):
		if data['user_'] not in self.USERS.keys():
			self.user_id +=1
			new_user = {}
			new_user['id'] = self.user_id
			new_user['username'] = data['user_']
			new_user['logged_in'] = 0
			new_user['session_id'] = ''
			new_user['pass'] = data['pass_']
			print(new_user)
			self.USERS[data['user_']] = new_user
			self.NOTIFS[data['user_']] = []  
			return 1
		else:
			# DEBUG, if you want to edit a password of user uncomment below 2 lines and use register page to change existing user's password
			# self.USERS[data['user_']]['pass'] = data['pass_']
			# print('pass_updated')
			return 0

	def login_me(self,data,sid):
		if data['user_'] in self.USERS.keys():
			if data['pass_'] != self.USERS[data['user_']]['pass']:
				return 0,'Wrong Password!'
			else:
				if self.USERS[data['user_']]['logged_in'] == 1:
					return 0,'User already Logged in!'
				else:
					self.USERS[data['user_']]['logged_in'] = 1
					self.USERS[data['user_']]['session_id'] = sid
					return 1,'User Logged in'
		else:
			return 0,data['user_'] + ' does not exists!'

	def get_notifs(self,username):
		lst = self.NOTIFS[username][:]
		self.NOTIFS[username] = []
		notif_mess = []
		for n in lst:
			notif_mess.append(self.MESSAGES[n])
		return notif_mess

	def get_online_list(self):
		lst_html = '<p>'
		usr_drop = ['SELECT USER']
		for u in self.USERS.keys():
			usr_drop.append(u)
			if self.USERS[u]['logged_in']:
				cl = 'online'
			else:
				cl = 'offline'
			lst_html+='<a href="#userModal" role="button" data-toggle="modal" role="button" class="list-group-item ' + cl + '" onclick="get_details(this)">' + u +'</a>'
		lst_html += """</p><script>
		function get_details(ele)
		{
			username = ele.innerHTML;
			socket.emit('get_user_details',username);
		}
		</script>"""
		return lst_html,usr_drop

	def get_usr_details(self,username):
		return self.USERS[username]

	def show_db(self):
		print('')
		print('--==DATABASE==--')
		print('USERS')
		pp.pprint(self.USERS)
		print('MESSAGES')
		pp.pprint(self.MESSAGES)
		print('NOTIFS')
		pp.pprint(self.NOTIFS)
		print('--============--')
		print('')

	def log_out(self,username):
		self.USERS[username]['logged_in'] = 0
		self.USERS[username]['session_id'] = ''

	def update_notifs(self,mess_id):
		for u in self.USERS.keys():
			if self.USERS[u]['logged_in'] == 0:
				self.NOTIFS[u].append(mess_id)

	def new_message(self,mess):
		self.mess_id+=1
		mess['id'] = self.mess_id
		self.MESSAGES[self.mess_id] = mess
		self.update_notifs(self.mess_id)
		return self.mess_id

	def save_close(self):
		self.update_before_close()
		dict_ = {}
		dict_['USERS'] = self.USERS
		dict_['MESSAGES'] = self.MESSAGES
		dict_['NOTIFS'] = self.NOTIFS
		dict_['user_id'] = self.user_id
		dict_['mess_id'] = self.mess_id
		outfile = open(self.db_file,'wb')
		pickle.dump(dict_,outfile)
		outfile.close()
		print('DATABASE saved to pickle')

	def get_all_msgs_HTML(self,username):
		mess_htm = ''
		for ids in self.MESSAGES.keys():
			src = self.MESSAGES[ids]['src']
			dst = self.MESSAGES[ids]['dst']
			if self.MESSAGES[ids]['src'] == username:
				src = 'YOU'
			if self.MESSAGES[ids]['dst'] == username:
				dst = 'YOU'
			mess_htm = """
			<div id=mess_""" + str(ids) + """ class="panel panel-default">
	            <div class="panel-heading">
		            <p class="pull-right" style="color: #80808080;">""" + self.MESSAGES[ids]['time']+ """</p> 
		            <h4>""" + src +""" ► """ + dst + """</h4>
		        </div>
	            <div class="panel-body">
                    <p>""" + self.MESSAGES[ids]['msg'] + """</p>
                </div>
            </div>
			"""+mess_htm
		return mess_htm


			