#!python
from sqlalchemy import create_engine
from sqlalchemy_schemadisplay import create_schema_graph
from models.models import target_metadata
def get_admin_engine():
    # charbel:charbel@84.16.230.94:5437/matching_db
    return create_engine("postgresql://charbel:charbel@84.16.230.94:5437/matching_db", echo=False)


def generate_schema_diagram(output_path: str = "dbschema.png"):
    """
    Generate a schema diagram for the current database models.
    Args:
        output_path (str): Path to save the generated PNG file.
    """
    graph = create_schema_graph(
        metadata=target_metadata,
        show_datatypes=True,
        show_indexes=True,
        rankdir="RL",
        concentrate=True,
        engine=get_admin_engine(),
         
    )
 


    graph.write_png(output_path)


if __name__ == "__main__":
    generate_schema_diagram()
