#!python
from sqlalchemy_schemadisplay import create_schema_graph
from core.database import engine
from models.models import target_metadata

def generate_schema_diagram(output_path: str = 'dbschema.png'):
    """
    Generate a schema diagram for the current database models.
    Args:
        output_path (str): Path to save the generated PNG file.
    """
    graph = create_schema_graph(
        metadata=target_metadata,
        show_datatypes=True,
        show_indexes=True,
        rankdir='LR',
        concentrate=True,
        engine=engine
    )
    graph.write_png(output_path)
  
if __name__ == "__main__":
    generate_schema_diagram()
