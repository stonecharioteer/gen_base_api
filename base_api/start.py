from gen_api import app as application

if __name__ == "__main__":
    ## Instead launch a warning to prevent this.
    application.run("0.0.0.0", port=4000, debug=True,
                    threaded=True, use_reloader=True)
