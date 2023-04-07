def lambda_handler(event, context):
    import main

    r = main.main(event, context)
    return r
