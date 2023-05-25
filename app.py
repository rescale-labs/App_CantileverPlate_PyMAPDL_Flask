import os as os
import shutil

import numpy as np
from flask import Flask, render_template, request, url_for
from flask_restful import Api, Resource

import modules.pymapdl.bimetallic
from modules.constants import *

PREFIX = f"/notebooks/{os.getenv('RESCALE_CLUSTER_ID')}/"

app = Flask(__name__, static_url_path=f"{PREFIX}/static")

cwd = os.getcwd()
images = os.path.join(cwd, IMAGE_PATH)


def pyMapdl_vm35(L, t, e1, e2, c1, c2, T1, T2):
    # Launch
    mapdl, my_wdirnow = modules.pymapdl.bimetallic.my_mapdl_launch_in_cwd(
        NEW_WDIR_NAME, JNAME
    )

    # Solve
    png_path, uz_max = modules.pymapdl.bimetallic.solve_vm_35(
        images, mapdl, L, t, e1, e2, c1, c2, T1, T2
    )

    return [png_path, round(uz_max, 3)]


@app.route(PREFIX, methods=["POST", "GET"])
def calculator():
    my_Length = 10.0
    my_Thickness = 0.1
    my_mat1ex = 3.0e7
    my_mat2ex = 3.0e7
    my_mat1cte = 1e-5
    my_mat2cte = 2e-5
    my_tref = 70
    my_tamb = 170

    usum = ""
    image = ""
    roarkszmax = ""
    error1 = ""
    flag = ""

    if request.method == "POST":
        my_Length = float(request.form.get("Length"))
        my_Thickness = float(request.form.get("Thickness"))
        my_mat1ex = float(request.form.get("mat1ex"))
        my_mat2ex = float(request.form.get("mat2ex"))
        my_mat1cte = float(request.form.get("mat1cte"))
        my_mat2cte = float(request.form.get("mat2cte"))
        my_tref = float(request.form.get("tref"))
        my_tamb = float(request.form.get("tamb"))
        p_run = pyMapdl_vm35(
            my_Length,
            my_Thickness,
            my_mat1ex,
            my_mat2ex,
            my_mat1cte,
            my_mat2cte,
            my_tref,
            my_tamb,
        )
        print(RUN_COMPLETE)

        shutil.move(p_run[0], FINAL_IMAGE_PATH)
        image = FINAL_IMAGE_PATH
        usum = p_run[1]
        flag = 1
        print(image)
        print(usum)

        roarkszmax = modules.pymapdl.bimetallic.roarks_vm_35(
            my_Length,
            my_Thickness,
            my_mat1ex,
            my_mat2ex,
            my_mat1cte,
            my_mat2cte,
            my_tref,
            my_tamb,
        )

        if not abs(usum) > 0.0:
            error1 = 0.000
            print("error1 " + str(error1))
        else:
            error1 = ((p_run[1] - roarkszmax) / p_run[1]) * 100
            error1 = round(error1, 3)
            print("error is " + str(error1))
        print("roarks is " + str(roarkszmax))

    return render_template(
        "inputpage.html",
        Flag=flag,
        TotalDeformation=usum,
        SolveStatus="Solved",
        RoarksZmax=roarkszmax,
        error=error1,
        output_image_url=image,
        L2=my_Length,
        t2=my_Thickness,
        E21=my_mat1ex,
        E22=my_mat2ex,
        c21=my_mat1cte,
        c22=my_mat2cte,
        T1=my_tref,
        T2=my_tamb,
        route_prefix=PREFIX,
    )


# Resale App discovery endpoint
class RescaleAppDiscovery(Resource):
    def get(self):
        return {
            "name": "Bimetallic Layered Cantilever Plate with Thermal Loading",
            "description": "An example of a Rescale App using ANSYS PyMAPDL module and the Flask web framework",
            "helpUrl": "https://github.com/rescale-labs/App_CantileverPlate_PyMAPDL_Flask",
            "icon": url_for("static", filename="app_icon.png"),
            "supportEmail": "support@rescale.com",
            "webappUrl": PREFIX,
            "isActive": True,
        }


api = Api(app)
api.add_resource(RescaleAppDiscovery, f"/{PREFIX}/.rescale-app")

if __name__ == "__main__":
    app.run(debug=True)
