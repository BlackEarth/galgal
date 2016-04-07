
import tornado.web
from bl.dict import Dict
from .application import RequestHandler
from amp.emailer import Emailer

class SignupHandler(RequestHandler):
    def get(self):
        c = self.c
        if self.url.qargs.key is not None:
            self.db.init_session()
            invitation = self.db.session.query(self.db.Invitation).filter_by(key=self.url.qargs.key).first()
            if self.debug==True: print("SIGNUP INVITATION: %r" % invitation)
            if invitation is None:
                self.redirect('/'+URL+'/signup')
            else:
                c.user = self.db.User(email=invitation.email, role=invitation.role)
        # without an invitation, only a logged in admin user can do a signup.
        elif self.session.user is None:
            self.session.notice = "Please login before continuing."
            self.redirect('/acct/login?ret='+ str(self.url))
        elif self.session.user.role != 'admin':
            raise tornado.web.HTTPError(401)
        else:
            c.user = self.db.User()
        self.render(URL+'/signup.html')

    def post(self):
        c = self.c
        self.db.init_session()
        post_args = self.arguments_to_dict()
        if self.url.qargs.key is not None:
            invitation = self.db.session.query(self.db.Invitation).filter_by(key=self.url.qargs.key).first()
        c.user = self.db.User(**Dict(__prefix__='user_', **post_args))
        c.errors = c.user.register(self.db.session)
        invitation.accepted = 'now()'
        if self.debug==True: 
            print("User: %r" % c.user)
            print("Errors: %r" % c.errors)
        if c.errors == {}:
            emailer = Emailer(self.config, URL+'/signup_mail.txt')
            result = emailer.send_message(c.user.email, 'Verify your Biblicity Registration', c=c)
            if result is None or self.config.Email.delivery == 'test':
                if self.debug==True: print(result)
                self.session.notice = "Thank you for registering. Please check your email (%s) for instructions to verify your account." % c.user.email
                if self.config.Email.delivery == 'test': 
                    self.session.notice += (result or '')
                self.redirect('/'+URL+'/login')
            else:
                self.session.error = "Unfortunately, the registration could not be saved at this time. Please try again later." 
                # **TODO: This should trigger an email to the support team.**
        self.render(URL+'/signup.html')


class LoginHandler(RequestHandler):
    @tornado.web.removeslash
    def get(self):
        self.render(URL+'/login.html')

    def post(self):
        user = Dict()
        post_args = self.arguments_to_dict()
        if self.debug==True: print("post_args:", post_args)
        user.update_from_prefix('user_', **post_args)
        self.db.init_session()
        user = self.db.User.authenticate(self.db.session, user.email, user.password)
        if self.debug==True: print(user)
        if user is not None:
            if post_args.keep_signed_in == 'on':    # **NOT WORKING: The sign-on doesn't survive browser shutdown.*
                expires_days = 30
            else:
                expires_days = None
            self.init_session(user=Dict(username=user.username, email=user.email, role=user.role), expires_days=expires_days)
            self.session.notice = "Welcome, " + user.username + "!"
            if self.debug==True: print('session:', self.session)
            self.redirect(self.url.qargs.ret or post_args.ret or '/users/'+user.username)
            return
        else:
            self.clear_session()
            self.session.error = "We're sorry, there was a problem with your login. Have you verified your email address? Please refer to your login information and try again."
            self.render(URL + '/login.html')

class InviteUserHandler(RequestHandler):
    @RequestHandler.require_admin
    @tornado.web.removeslash
    def get(self):
        c = self.c
        self.db.init_session()
        c.invitation = Dict()
        self.render(URL+'/invite_user.html')

    @RequestHandler.require_admin
    @tornado.web.removeslash
    def post(self):
        c = self.c
        self.db.init_session()
        post_args = self.arguments_to_dict()
        c.invitation = self.db.Invitation(**Dict(__prefix__='invitation_', **post_args))
        c.errors = c.invitation.invite(self.db.session)
        if self.debug==True: 
            print("Invitation: %r" % c.invitation)
            print("Errors: %r" % c.errors)
        if c.errors == {}:
            emailer = Emailer(self.config, URL+'/invite_user_mail.txt')
            result = emailer.send_message(c.invitation.email, 'Invitation to Biblicity', c=c)
            if result is None or self.config.Email.delivery == 'test':
                if self.debug==True: print(result)
                self.session.notice = c.invitation.email + ' has been invited!'
                if self.config.Email.delivery == 'test': 
                    self.session.notice += (result or '')
                c.invitation = Dict()
            else:
                self.session.error = "Unfortunately, the invitation could not be sent at this time. Please try again later." 
                self.db.session.delete(c.invitation)
                # **TODO: This should trigger an email to the support team.**
        self.render(URL+'/invite_user.html')

class VerifyUserHandler(RequestHandler):
    @tornado.web.removeslash
    def get(self, username, code):
        self.db.init_session()
        if self.debug==True:
            print('username:', username)
            print('code:', code)
        user = self.db.User.verify(self.db.session, username, code)
        if user is not None:
            self.session.notice = "Thank you for verifying your account! Please login to continue."
            self.redirect('/'+URL+'/login')
        else:
            self.session.error = "Unfortunately, your account could not be verified at this time. Please try again later."
            # **TODO: Notify support! For some reason the verification code is not correct.**
            self.redirect('/')

class ResetPasswordHandler(RequestHandler):
    @tornado.web.removeslash
    def get(self):
        self.render(URL+'/resetpwd.html')

    @tornado.web.removeslash
    def post(self):
        self.db.init_session()
        user = self.db.session.query(self.db.User).filter_by(email=self.arguments_to_dict().user_email).first()
        if user is None:
            self.session.error = "Sorry, there is no account with that email address."
            self.redirect('/'+URL+'/resetpwd')
        else:
            emailer = Emailer(self.config, URL+'/resetpwd_mail.txt')
            result = emailer.send_message(user.email, 'Reset Biblicity Password', user=user)
            if result is None or self.config.Email.delivery == 'test':
                self.session.notice = "Please check your email for further instructions on resetting your Biblicity password."
                if self.config.Email.delivery == 'test': self.session.notice += result
                self.redirect('/')
            else:
                self.session.error = "Sorry, the password reset email could not be sent. Please try again later."
                # **TODO: Notify support! The email should have been sent.**

class NewPasswordHandler(RequestHandler):
    @tornado.web.removeslash
    def get(self, username, code):
        self.db.init_session()
        user = self.db.session.query(self.db.User).filter_by(username=username).first()
        if user is not None and user.password_reset_code()==code:
            self.render(URL+'/newpwd.html')
        else:
            self.session.error = "Sorry, your password could not be reset at this time. Please try again later."
            self.redirect('/')

    @tornado.web.removeslash
    def post(self, username, code):
        c = self.c
        post_args = self.arguments_to_dict()
        c.user = Dict(__prefix__='user_', **post_args)
        self.db.init_session()
        user = self.db.session.query(self.db.User).filter_by(email=c.user.email).first()
        if user is not None and user.password_reset_code()==code:
            user.set_password(post_args.user_password)
            self.session.notice = "Your password was successfully changed. Please login to continue."
            self.redirect('/'+URL+'/login')
        else:
            self.session.error = "Sorry, your password could not be changed at this time. Please try again later."
            self.redirect('/')

class LogoutHandler(RequestHandler):
    @tornado.web.removeslash
    def get(self):
        self.clear_session()
        self.session.notice = "You’re now logged out."
        self.redirect('/')


# ------------------------------------------------------------
# ROUTES

routes = [
    ('/'+URL+'/signup/?', SignupHandler),
    ('/'+URL+'/login/?', LoginHandler),
    ('/'+URL+'/logout/?', LogoutHandler),
    ('/'+URL+'/invite_user/?', InviteUserHandler),  
    ('/'+URL+'/verify/(?P<username>\w+)/(?P<code>\w+)/?', VerifyUserHandler),
    ('/'+URL+'/resetpwd/?', ResetPasswordHandler),
    ('/'+URL+'/newpwd/?(?P<username>\w+)?/?(?P<code>\w+)?/?', NewPasswordHandler),  
]
