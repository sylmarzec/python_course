import subprocess, os

OF_DIR ="/opt/openfoam231"
PARAVIEW ="/home/wgryglas/Applications/ParaView-4.3.1-Linux-64bit/bin/paraview"



def runBashCommands(cwd, output, *args):
    """
    Function for running system process through bash shell
    :param cwd: current working directory for process
    :param output: True/False, indicate if output shall be printed into console
    :param args: variable number of commands to be executed in the shell
    :return: None
    """
    command = "; ".join(args)
    process = subprocess.Popen(command, cwd=cwd, executable="/bin/bash", shell=True, stdout=subprocess.PIPE)

    com = process.communicate()[0]
    if output:
        print com


def runCase(casePath, output=True,  application="simpleFoam", openfoamDir=None):
    """
    Function which runs OpenFOAM case. Default OpenFOAM binaries are selected from OF_DIR variable. Eg. you can set
    this location once for whole python file by typing of.OF_DIR = "your/path/to/openfoam"
    :param casePath: Path to the case director which should be computed by OF application
    :param output: True/False, indicate if output shall be printed into console
    :param application: Name of OpenFOAM application to be used
    :param openfoamDir: optional argument, sets OpenFOAM path if different then OF_DIR should be used
    :return:
    """
    if not openfoamDir:
        openfoamDir = OF_DIR
    bashrc = os.path.join(openfoamDir, "etc", "bashrc")
    runBashCommands(casePath, output, "source "+bashrc, application)


def clearCase(casePath, output=True, openfoamDir=None):
    """
    Removes all case data, like mesh, results, postProcessing
    :param casePath: OpenFOAM case directory to be cleaned
    :param output: True/False, indicate if output shall be printed into console
    :param openfoamDir:
    :return:
    """
    if not openfoamDir:
        openfoamDir = OF_DIR
    clearFunctioinsFile = os.path.join(openfoamDir, "bin","tools","CleanFunctions")
    runBashCommands(casePath, output, "source "+clearFunctioinsFile, "cleanCase")


def clearResults(casePath, output=True, openfoamDir=None):
    """
    Removes only results data stored in time directories (despite 0 time which is actualy the initial and boundary
    conditions.
    :param casePath: OpenFOAM case directory to be cleaned
    :param output: True/False, indicate if output shall be printed into console
    :param openfoamDir: optional argument, sets OpenFOAM path if different then OF_DIR should be used
    :return:
    """
    if not openfoamDir:
        openfoamDir = OF_DIR
    clearFunctioinsFile = os.path.join(openfoamDir, "bin","tools","CleanFunctions")
    runBashCommands(casePath, output, "source "+clearFunctioinsFile, "cleanTimeDirectories", "rm -r postProcessing")


def createBlockMesh(casePath, output=True, openfoamDir=None):
    """
    Runs the blockMesh OpenFOAM appliction, which aims to create mesh,
    :param casePath: OpenFOAM case directory to be cleaned
    :param output: True/False, indicate if output shall be printed into console
    :param openfoamDir: optional argument, sets OpenFOAM path if different then OF_DIR should be used
    :return:
    """
    if not openfoamDir:
        openfoamDir = OF_DIR
    bashrc = os.path.join(openfoamDir, "etc", "bashrc")
    runBashCommands(casePath, output, "source "+bashrc, "blockMesh")


def getStateFile(casePath):
    """
    Function returning path to the postprocessing paraview state file in reference to case directory.
    :param casePath: OpenFOAM case directory to be cleaned
    :return: string, path to the postprocessing paraview state file
    """
    return os.path.join(casePath,"postprocessing.pvsm")

def __createStateFile__(casePath):
    name = os.path.basename(casePath)
    name += ".foam"
    toReplacePath="FOAM_FILE"
    post = os.path.join(casePath, name)

    toReplaceName = "FOAM_NAME"

    open(os.path.join(casePath,name),"w").close()

    state=getStateFile(casePath)
    state2=os.path.join(casePath,"postprocessing2.pvsm")

    lines =[]
    changed=False
    with open(state, "r") as f:
        for l in f:
            if toReplacePath in l:
                l = l.replace(toReplacePath, post)
                changed=True

            if toReplaceName in l:
                l = l.replace(toReplaceName, name)
                changed=True

            lines.append(l)

    if not changed:
        return

    print "writing state file..."

    with open(state2,"w") as f2:
        f2.writelines(lines)

    os.remove(state)
    os.rename(state2, state)




def parview(casePath, paraview=None):
    """
    Runs the ParaView application with loaded data from provided case file
    :param casePath: OpenFOAM case directory to be cleaned
    :param paraview: optional path for ParaView application file (e.g.: obtained by  "which paraview" command)
    :return: None
    """
    if not paraview:
        paraview = PARAVIEW
    __createStateFile__(casePath)
    state=os.path.join(casePath,"postprocessing.pvsm")
    runBashCommands(casePath, False, paraview+" --state="+state)



def hasMesh(case):
    """
    Function checks if mesh is already craeted in provided case path
    :param case:  OpenFOAM case directory to be cleaned
    :return:True/False
    """
    polyMesh = os.path.join(case, "constant", "polyMesh")
    required = ["points", "boundary", "faces", "owner", "neighbour"]
    for f in os.listdir(polyMesh):
        if f in required:
            required.remove(f)

    return len(required) == 0



# Warning: to use this function Paraview and VTK from paraview location
# (eg. /opt/paraview/lib/site-packages and /opt/paraview/lib/site-packages/vtk)
# need to be added to PYTHONPATH,
# Also you should add to LD_LIBRARY_PATH paraview libs path

def view(casePath, colorby=None):
    """
    Display
    :param casePath: OpenFOAM case directory to be cleaned
    :param colorby: Define the field which should be displayed
    :return:None
    """
    from paraview.simple import *

    if not GetActiveSource():
        __createStateFile__(casePath)
        servermanager.LoadState(getStateFile(casePath))
        SetActiveView(GetRenderView())

        for source in GetSources():
            # help(GetSources()[source])
            SetActiveSource(GetSources()[source])
        if colorby:
            ColorBy(value=colorby)
            UpdateScalarBars()
    else:
        GetActiveSource().Refresh()

    Render()


def view2(casePath, colorby=None):
    from paraview.simple import *
    import numpy as np

    if not GetActiveSource():
        PVServer = "localhost"
        reader = OpenDataFile(os.path.join(casePath, os.path.basename(casePath)+".foam"))
        v = GetActiveViewOrCreate('RenderView')

        readerRep = GetRepresentation(view=v)
        readerRep.Representation='Surface With Edges'

        animationScene1 = GetAnimationScene()
        animationScene1.UpdateAnimationUsingDataTimeSteps()
        animationScene1.GoToLast()


        if not colorby:
            colorby = "U"


        ColorBy(readerRep, ("POINTS",colorby))
        readerRep.RescaleTransferFunctionToDataRange(True)


        lt = AssignLookupTable(reader.PointData.GetArray(colorby), 'Blue to Red Rainbow', rangeOveride=reader.PointData.GetArray(colorby).GetRange())
        lt.VectorMode = 'Magnitude'
        readerRep.LookupTable = lt
        readerRep.SetScalarBarVisibility(GetActiveView(), True)

        uLUT = GetColorTransferFunction('U')

        # get opacity transfer function/opacity map for 'U'
        uPWF = GetOpacityTransferFunction('U')



        GetActiveView().CameraParallelProjection = 1
        GetActiveView().CameraParallelScale = 1.0

        GetRenderView().ViewSize = [800, 600];

        readerRep.RescaleTransferFunctionToDataRange(False)


        Render()
        #SetViewProperties( Projection="Parallel" )

    else:
        GetActiveSource().Refresh()


def saveCurrentImage(fname, casePath, colorby=None):
    """

    :param fname:
    :param casePath:
    :param colorby:
    :return:
    """
    view(casePath,colorby)
    from paraview.simple import WriteImage
    WriteImage(fname)



