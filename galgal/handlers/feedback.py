from amplitude.controller import Controller

class Feedback(Controller):
    actions=['new', 'index']
    
    def new(c, req):
        if c.unauthorized(req): return c.unauthorized(req)
        if req.env['REQUEST_METHOD'] == 'POST':
            req.db = c.db or c.config.db()
            item = c.models.Feedback(req.db, **req.params)
            item.insert()
            emailer = c.emailers.Feedback(c.config, c.template_lookup)
            msg = emailer.feedback_mail(item)
            emailer.send(msg)
            return c.render('/feedback/submitted.mako')
        return c.render('/feedback/new.mako')
        
    def index(c, req):
        if c.unauthorized_except_admin(req): return c.unauthorized_except_admin(req)
        req.db = c.db or c.config.db()
        items = c.models.Feedback(req.db).select(orderby="inserted desc")
        return c.render('/feedback/index.mako', items=items)

    # -- util --         
    def unauthorized(c, req):
        """Return None if authorized, redirect if unauthorized"""
        req.init_session()
        if not req.session.has_key('user'):
            return c.response.redirect(c.site_uri+'/user/login?returnpath='+req.uri)

    def unauthorized_except_admin(c, req):
        req.init_session()
        if not req.session.has_key('user') or req.session.user != c.config.Site.admin:
            return c.response.redirect(c.site_uri+'/user/login?returnpath='+req.uri)