#!/usr/bin/env python3
import os

from siliconcompiler import Design, ASIC
from siliconcompiler.targets import skywater130_demo
from siliconcompiler.flows import asicflow
from siliconcompiler import StdCellLibrary
from siliconcompiler.tools.yosys import YosysStdCellLibrary
from siliconcompiler.tools.openroad import OpenROADStdCellLibrary
from siliconcompiler.tools.klayout import KLayoutLibrary

from pathlib import Path
from siliconcompiler import StdCellLibrary
import pprint

# Working directory
workdir = "."
os.makedirs(workdir, exist_ok=True)

# ---------------- Step 1: Create Verilog for module A ----------------
verilog_a = """
module A(
    input  wire       clk,
    input  wire[31:0] a,
    input  wire[31:0] b,
    output reg [31:0] y
);

  always @ (posedge clk) begin
    y = a & b; // simple AND gate
  end
endmodule
"""

file_a = os.path.join(workdir, "A.v")
with open(file_a, "w") as f:
  f.write(verilog_a)

clk_file = os.path.join(workdir, "top.sdc")
with open(clk_file, "w") as f:
    f.write(f"create_clock -name clk -period 100 [get_ports clk]\n")

# ---------------- Step 2: Synthesize, place & route module A ----------------
A = "A"
design_a = Design(A)

design_a.set_dataroot(A, __file__)
design_a.add_file(f"{A}.v", fileset='verilog')
design_a.set_topmodule(A, fileset='verilog')

project_a = ASIC(design_a)
project_a.add_fileset(['verilog'])
skywater130_demo(project_a)

project_a.run()
project_a.summary()

class ModA(YosysStdCellLibrary, OpenROADStdCellLibrary, KLayoutLibrary):
  def __init__(self, modA):
    super().__init__()
    self.set_name("modA") # I want to use A as the name but it conflicts with the existing A code

    self.add_asic_pdk(modA.get("asic", "pdk"))

    with self.active_fileset("models.physical"):
      self.add_file("./build/A/job0/write.views/0/outputs/A.lef")
      self.add_file("./build/A/job0/write.views/0/outputs/A.slow.lib")
      self.add_file("./build/A/job0/write.gds/0/outputs/A.gds")
      self.add_asic_aprfileset()

    with self.active_fileset("models.timing.nldm"):
      self.add_file("./build/A/job0/write.views/0/outputs/A.slow.lib")
      self.add_asic_libcornerfileset("generic", "nldm")

# If needed:
#    with self.active_fileset("openroad.powergrid"):
#      self.add_file(path_base / "apr" / "openroad" / "pdngen.tcl")
#      self.add_openroad_powergridfileset()
#
#    with self.active_fileset("openroad.globalconnect"):
#      self.add_file(path_base / "apr" / "openroad" / "global_connect.tcl")
#      self.add_openroad_globalconnectfileset()

# ---------------- Step 3: Create Verilog for module B (instantiates A twice) ----------------
verilog_b = """
module B(
    input  wire       clk,
    input  wire[31:0] a1,
    input  wire[31:0] b1,
    input  wire[31:0] a2,
    input  wire[31:0] b2,
    output reg[31:0] y1,
    output reg[31:0] y2
);
    // Instantiate module A twice as hard macros

    A u1 (.clk(clk), .a(a1), .b(b1), .y(y1));
    A u2 (.clk(clk), .a(a2), .b(b2), .y(y2));
endmodule
"""

file_b = os.path.join(workdir, "B.v")
with open(file_b, "w") as f:
    f.write(verilog_b)

# ---------------- Step 4: Create SC Chip for B ----------------
B = "B"
design_b = Design(B)

design_b.set_dataroot(B, __file__)
design_b.add_file(f"{B}.v", fileset='verilog')
design_b.set_topmodule(B, fileset='verilog')

project_b = ASIC(design_b)
project_b.constraint.area.set_diearea_rectangle(1000, 1000)
#pprint.pprint(project_b.getdict())

project_b.add_fileset(['verilog'])
project_b.add_asiclib(ModA(project_a))
skywater130_demo(project_b)
project_b.run()
project_b.summary()
