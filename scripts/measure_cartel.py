"""Mide el proyecto aislado del cartel, no el entorno de desarrollo."""
from scripts import measure_demo

measure_demo.PROJECT = 'soundgraph-cartel-20261126'
measure_demo.PORT = 18136
measure_demo.ORIGIN = f'http://{measure_demo.HOST}:{measure_demo.PORT}'

if __name__ == '__main__':
    measure_demo.main()
