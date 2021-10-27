from app.auth_external import bp, services
from flask_login import current_user, login_required

# a universal path for logging into services
@bp.route('/auth/<service>', methods=['GET', 'POST'])
@login_required
def auth(service):
    # if request.method == 'POST'
    if current_user.is_authenticated:
        if service == 'spotify':
            sp_oauth = current_user.log_in(service) # creates a new sp_oauth object everytime a user logs in
            auth_url = sp_oauth.get_authorize_url() # passes the authorization url into a variable
            return redirect(auth_url)
        elif service == 'soundcloud':
            return f'> {service} auth under construction <'
        elif service == 'youtube':
            return f'> {service} auth under construction <'
    else:
        return redirect(url_for('auth_internal.login'))
