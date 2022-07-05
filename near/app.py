from fastapi import FastAPI

from near import transactions


class App(FastAPI):
    pass


app = App()


@app.get("/_health")
def read_root():
    return True


app.include_router(transactions.controllers.router)
