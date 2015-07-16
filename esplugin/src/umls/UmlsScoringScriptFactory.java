package umls;

import java.util.Map;
import org.elasticsearch.script.ExecutableScript;
import org.elasticsearch.script.NativeScriptFactory;

public class UmlsScoringScriptFactory implements NativeScriptFactory{
@Override
  public ExecutableScript newScript(Map<String, Object> params) {
    return new UmlsScoringScript(params);
  }
}
