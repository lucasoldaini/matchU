package umls;

import java.util.Map;

import org.elasticsearch.script.AbstractDoubleSearchScript;
import org.elasticsearch.index.fielddata.ScriptDocValues;
import org.elasticsearch.search.lookup.*;

public class UmlsScoringScript extends AbstractDoubleSearchScript{

  Double factor;
  String field;

  public UmlsScoringScript(Map<String, Object> params){
    factor = Double.parseDouble( (String) params.get("factor"));
    field = (String) params.get("field");
  }

  @Override
  public double runAsDouble() {
    float score = 3;
            // first, get the IndexField object for the field.

    doc();
    IndexField indexField = indexLookup().get(field);
    System.out.println(indexField.toString());

    return score;
  }
}
