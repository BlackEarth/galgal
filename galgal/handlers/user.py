
from amplitude.controller import Controller
from amplitude.dict import Dict

class User(Controller):
    actions = ['index', 'signup', 'verify',
                'login', 'login_successful', 'logout', 'resetpwd']
                
    def index(c, req):
        req.init_session()
        return c.render('/user/index.mako')

    def signup(c, req):
        """provide a signup form and process it."""
        req.init_session()
        c.db = c.db or c.config.db()
        user = c.models.User(c.db)
        if req.POST():
            # see about registering this new user (validations in the model).
            user.set_attribs(prefix='user_', **req.params)
            print("signup:", user)
            errors = user.register()
            req.session.user = user.email
            c.response.set_cookie('session_id', req.session.id, path=c.config.Site.path or '/')
            if errors is None:
                # send signup notice if we have an emailer.
                emailer = c.emailers.User(c.config, c.template_lookup)
                msg = emailer.signup_mail(user=user)
                mail_exception = emailer.send(msg)
                if mail_exception is not None:
                    # rollback the registration
                    user.delete(where="email=%s" % user.quote(user.email))
                    req.reset_session()
                    # log errors
                    print("mail exception:", mail_exception)
                    req.session.error = "We're sorry, we were unable to complete your registration at this time. Please try again later."
            else:
                req.session.error = ' '.join(errors)
            req.session.save()
            if req.session.error is None:
                return c.render('/user/signup_complete.mako', user=user)
            else:
                return c.render('/user/signup.mako', user=user)
        else:
            # not POST, so give the signup form if not actually logged in
            if req.session.user is not None and c.models.User(c.db).select_one(email=req.session.user) is not None:
                req.session.notice = "You're already signed up and logged in. Welcome!"
                return c.response.redirect(req.params.returnpath or c.site_uri)
            return c.render('/user/signup.mako', user=user, errors=None)
        
    def verify(c, req):
        """verify the given user. Works with a GET request using the user's id and verification key."""
        req.init_session()
        if req.params.id is not None:
            c.db = c.db or c.config.db()
            req.session.error=c.models.User(c.db).verify(id=req.params.id, key=req.params.key)
            if req.session.error is None:
                req.session.notice = "Thank you for verifying your account. You can now login."
                return c.login(req)
            else:
                return c.render('/user/verify_incomplete.mako')
        
    def login(c, req):
        """try to log the user into the site."""
        req.init_session()
        c.db = c.db or c.config.db()
        if req.env['REQUEST_METHOD'] == 'POST':
            attribs = Dict(); attribs.set_attribs(prefix='user_', **req.params)
            user = c.models.User(c.db).authenticate(**attribs)
            if user is not None:
                # successful login
                req.session.user = user.email
                if c.config.Site.debug==True: print("login user:", req.session.user)
                req.session.save()
                c.response.set_cookie('session_id', req.session.id, path=c.config.Site.path or '/')
                return c.response.redirect(req.params.returnpath or c.site_uri+'/user/login_successful')
            else:
                req.session.error = "We're sorry, there was a problem with your login. Please refer to your login information and try again."
                return c.render('/user/login_unsuccessful.mako', user=c.models.User(c.db))
        else:
            if req.session.user is not None and c.models.User(c.db).select_one(email=req.session.user) is not None:
                req.session.notice = "You're already logged in. Welcome!"
                return c.response.redirect(req.params.returnpath or c.site_uri)
            if req.params.embedded=='True':
                return c.render('/user/login_form.mako', user=c.models.User(c.db))
            else:
                return c.render('/user/login.mako', user=c.models.User(c.db))
        
    def login_successful(c, req):
        req.init_session()
        return c.render('/user/login_successful.mako')

    def logout(c, req):
        """logout the current user by resetting the session."""
        req.init_session()
        req.reset_session()
        c.response.delete_cookie('session_id', path=c.config.Site.path or '/')
        return c.render('/user/logout.mako')

    def resetpwd(c, req):
        req.init_session()
        if req.env['REQUEST_METHOD'] == 'POST':
            # send a new password -- need an emailer.
            c.db = c.db or c.config.db()
            user = c.models.User(c.db).select_one(email=req.params.user_email)
            if user is not None:
                print("reset password:")
                print("  user:", user.email)
                # generate and send a new password
                newpwd = c.models.User.random_password()
                user.set_password(newpwd)
                try:
                    user.update()
                except:
                    req.session.error = "Unable to reset password."
                    print("  NOT RESET")
                    return c.render('/user/resetpwd.mako')
                user.password = newpwd
                emailer = c.emailers.User(c.config, c.template_lookup)
                msg = emailer.new_pwd_mail(user=user)
                mail_exception = emailer.send(msg)
                if mail_exception is not None:
                    print("  MAIL EXCEPTION")
                    req.session.error = "We're sorry, your password was reset, but the mail was unable to go through. Please try resetting your password again later."
                else:
                    print("  RESET")
                    req.session.notice = "Your password has been reset -- please check your email to login with your new password."
                    req.env['REQUEST_METHOD'] = 'GET'
                    return c.login(req)
            else:
                print("reset password: User not found.")
                req.session.notice = "User not found."
        
        # GET and POST fallback
        return c.render('/user/resetpwd.mako')
        
