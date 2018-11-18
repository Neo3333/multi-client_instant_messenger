# -*- coding: utf-8 -*-

from chat_utils import *
import random
import pickle as pkl
import indexer
import time

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s
        self.private_number = random.randint(10,100)
        self.clock_size = 11
        self.base = 2
        self.shared_secret = 0
        self.is_encrypted = False
        self.personal_history = {}
        self.chatting_start_time = 0
        self.chatting_ending_time = 0
        self.preference = {}
    
    def compute_PPN_1(self, base, clock_size, private_number):
        return (base**private_number)%clock_size
    
    def compute_PPN_2(self, received_PPN, clock_size, private_number):
        return (received_PPN**private_number)%clock_size
    
    def cripta(self, text, shared_secret):
        encrypted_text = ""
        for char in text:
            encrypted_text += " " + str(ord(char)+shared_secret)
        return encrypted_text
  
    def decripta(self, text, shared_secret):
        list_to_decrypt = text.split(" ")
        decrypted_text = ""
        for alpha in list_to_decrypt[0:]:
            decrypted_text += chr(int(alpha)-shared_secret)
        return decrypted_text 
          
            
    def set_state(self, state):
        self.state = state
        
    def get_state(self):
        return self.state
    
    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me
        
    def connect_to(self, peer):
        msg = M_CONNECT + peer
        mysend(self.s, msg)
        response = myrecv(self.s)
        if response == (M_CONNECT+'ok'):
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response == (M_CONNECT + 'busy'):
            self.out_msg += 'User is busy. Please try again later\n'
        elif response == (M_CONNECT + 'hey you'):
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = M_DISCONNECT
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def proc(self, my_msg, peer_code, peer_msg):
        self.out_msg = ''
        if self.state == S_LOGGEDIN:
            if len(my_msg) > 0:
                
                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE
                    
                elif my_msg == 'time':
                    mysend(self.s, M_TIME)
                    time_in = myrecv(self.s)
                    self.out_msg += "Time is: " + time_in
                            
                elif my_msg == 'who':
                    mysend(self.s, M_LIST)
                    logged_in = myrecv(self.s)
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in
                            
                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        
                        self.chatting_start_time = time.time()
                        
                        print("Current encryption status: ", self.is_encrypted)
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'
                        
                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, M_SEARCH + term)
                    search_rslt_server = myrecv(self.s)[1:].strip()
                    search_rslt_prs_history = ''
                    
                    client_name = self.me
                    if client_name not in self.personal_history.keys():
                        try:
                            self.personal_history[client_name] = pkl.load(open(client_name+'.idx','rb'))
                            
                        except IOError:
                            self.personal_history[self.me] = indexer.Index(self.me)
                    
                    
                    search_rslt_prs_history += (self.personal_history[client_name].search(term)).strip()
                    
                            
                    total_search = search_rslt_server + search_rslt_prs_history
                    if (len(total_search)) > 0:
                        self.out_msg += 'Public conversation history:' + '\n' + search_rslt_server + '\n\n' + \
                                        'Private conversation history:' + '\n' + search_rslt_prs_history + '\n\n'
                      
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'
                        
                elif my_msg == 'all history':
                    mysend(self.s, M_HISTORY)
                    rslt = myrecv(self.s)[1:].strip()
                    if (len(rslt)) > 0:
                        self.out_msg += rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'
                        
                        
                elif my_msg[0] == 'p':
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, M_POEM + poem_idx)
                    poem = myrecv(self.s)[1:].strip()
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'
                    
            if len(peer_msg) > 0:
                if peer_code == M_CONNECT:
                    self.peer = peer_msg
                    self.out_msg += 'Request from ' + self.peer + '\n'
                    self.out_msg += 'You are connected with ' + self.peer
                    print('Current encryption status: ', self.is_encrypted)
                    self.out_msg += '. Chat away!\n\n'
                    self.out_msg += '------------------------------------\n'
                    self.state = S_CHATTING
                    
                
                    
        elif self.state == S_CHATTING:
            if len(my_msg) > 0: # my stuff going out
                
                if  my_msg.rstrip(my_msg[20:]) == "secure my chat with ":
                    if self.is_encrypted == True:
                        print("please unsecure yourself first")
                    else:
                        name = my_msg[20:]
                        public_private_number = str(self.compute_PPN_1(self.base,self.clock_size,self.private_number))
                        print("Securing the chat...")
                        mysend(self.s, M_SECURING+public_private_number+name)
                        self.is_encrypted = True
                        print("...")
                        print("...")
                        print("...")
                        print("SECURED")
                    
                if my_msg.rstrip(my_msg[19:]) != "secure my chat with" and my_msg.lower() != "unsecure my chat":
                    
                    if self.is_encrypted:
                        to_cript = "[-SECURED-" + self.me + "] " + my_msg
                        if self.me not in self.personal_history.keys():
                            try:
                                self.personal_history[self.me]=pkl(open(self.me+'.idx','rb'))
                            except:
                                self.personal_history[self.me] = indexer.Index(self.me)
                        to_save = text_proc(to_cript, '')
                        self.personal_history[self.me].add_msg_and_index(to_save)  
                        cripted_msg = self.cripta(to_cript, self.shared_secret)
                        mysend(self.s, M_SECURE_EXCHANGE + cripted_msg)
                    else:
                        mysend(self.s, M_EXCHANGE + "[" + self.me + "] " + my_msg)
                
                if my_msg.lower() == "unsecure my chat":
                    print()
                    print("Unsecuring the chat...")
                    self.is_encrypted = False
                    self.shared_secret = 0
                    print("...")
                    print("...")
                    print("...")
                    print("UNSECURED")
                    mysend(self.s, M_UNSECURING)
                
                if my_msg == 'bye':
                    if self.is_encrypted == True:
                        print("Unsecure before leaving the chat room")
                    else:
                        
                        self.preference = pkl.load(open(self.me + '.txt','rb'))
                        self.chatting_ending_time = time.time()
                        duration = self.chatting_ending_time - self.chatting_start_time

                        tml = list()
                        for key in self.preference:
                            tml.append(key)
                        if self.peer in tml:
                            self.preference[self.peer] += duration
                        else:
                            self.preference[self.peer] = duration

                        pkl.dump(self.preference, open(self.me + '.txt', 'wb'))
                        
                        
                        
                        self.disconnect()
                        self.state = S_LOGGEDIN
                        self.is_encrypted = False
                        self.shared_secret = 0
                        self.peer = ''
            
            if len(peer_msg) > 0:    
                if peer_code == M_CONNECT:
                    self.out_msg += "(" + peer_msg + " joined)\n"
                    print("Current encryption status: ", self.is_encrypted)
            
            #Securing-Unsecuring
                if peer_code == M_SECURING:
                    
                    #print(peer_msg[1:])
                    counter = 0
                    for alpha in peer_msg:
                        counter += 1
                        if alpha.isalpha():
                            break
                        
                    received_PPN = int(peer_msg[:counter-1])
 #                   print(received_PPN)
                    name = peer_msg[counter-1:]
 #                   print(name)
                    
                    self.shared_secret = self.compute_PPN_2(received_PPN, self.clock_size, self.private_number)
                    if self.is_encrypted == False:
                        public_private_number = str(self.compute_PPN_1(self.base,self.clock_size,self.private_number))
                        mysend(self.s, M_SECURING + public_private_number + name)
                        self.is_encrypted = True
                        print("Securing the chat...")
                        print("...")
                        print("...")
                        print("...")
                        print("SECURED")
                
                if peer_code == M_UNSECURING:
                    print()
                    self.is_encrypted = False
                    self.shared_secret = 0
                    print("Unscuring the chat...")
                    print("...")
                    print("...")
                    print("...")
                    print("UNSECURED")
                
                if peer_code == M_EXCHANGE:
                    self.out_msg += peer_msg

                if peer_code == M_SECURE_EXCHANGE:
                    if self.is_encrypted == True:
                        msg_to_decrypt = peer_msg[1:]
                        decrypted_msg = self.decripta(msg_to_decrypt, self.shared_secret)
                        if self.me not in self.personal_history.keys():
                            try:
                                self.personal_history[self.me]= pkl.load(open(self.me+'.idx','rb'))
                            except:
                                self.personal_history[self.me] = indexer.Index(self.me)
                        to_save = text_proc(decrypted_msg, '')
                        self.personal_history[self.me].add_msg_and_index(to_save)
                        self.out_msg += decrypted_msg
                    else:
                        self.out_msg += peer_msg
            
            if peer_code == M_DISCONNECT:
                self.state = S_LOGGEDIN
                self.is_encrypted = False
                self.shared_secret = 0

                
                
                

            
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)
            
        return self.out_msg
