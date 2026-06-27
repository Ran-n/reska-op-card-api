import uvicorn


def api():
    import sys
    import uvicorn.main

    uvicorn.main.main(
        ["reska_op_card_api.main:app", "--reload", *sys.argv[1:]]
    )
