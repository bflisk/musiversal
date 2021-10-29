def clear_cache():
    try:
        # needed to allow refresh token to be regenerated instead of being loaded from cache
        os.remove(r"/Users/brendan/Documents/code/universal/.cache")
    except:
        pass
