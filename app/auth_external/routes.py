from app.auth_external import bp, soundcloud, spotify, youtube

@bp.route('/auth/<service>')
def auth(service):
    return f'> {service} auth under construction <'
