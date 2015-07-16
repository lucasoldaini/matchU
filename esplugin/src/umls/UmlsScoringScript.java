package umls;

import java.util.*;
import java.io.IOException;


import org.elasticsearch.index.fielddata.ScriptDocValues;
import org.elasticsearch.script.AbstractDoubleSearchScript;
import org.elasticsearch.search.lookup.*;
import org.elasticsearch.script.ScriptException;

public class UmlsScoringScript extends AbstractDoubleSearchScript{

    String textFieldName;
    String ngramsFieldName;
    ArrayList <String> ngramsQuery;
    ArrayList <String> textQuery;
    Double alpha;
    Double beta;
    // Boolean normalize;

    public UmlsScoringScript(Map<String, Object> params){

        ngramsFieldName = (String) params.get("field_ngrams");
        textFieldName = (String) params.get("field_text");

        ngramsQuery = (ArrayList <String>) params.get("ngrams");
        textQuery = (ArrayList <String>) params.get("text");

        // normalize = (Boolean) params.get("normalize");

        // set alpha and beta to the same value if they are not
        // provided. If only one of the two is provided, the
        // other is set accordingly.
        alpha = (Double) params.get("alpha");
        beta = (Double) params.get("beta");
        if (alpha == null && beta == null){
            alpha = beta = 0.5;
        } else if (alpha == null) {
            alpha = 1 - beta;
        } else if (beta == null) {
            beta = 1 - alpha;
        }


        if (alpha < 0.0 || alpha > 1.0 || beta < 0.0 || beta > 1.0 ){
            throw new ScriptException("Alpha or beta not in range [0, 1]");
        }

        // if (normalize == null) {
        //     normalize = false;
        // }

    }

    @Override
    public double runAsDouble() {
        try{
            double alpha_score = 0.0;
            double beta_score = 0.0;

            // System.out.print(ngramsFieldName + "; ");
            // System.out.println(textFieldName + " ");

            // first, get the IndexField object for the ngram and text fields.
            IndexField ngramsField = indexLookup().get(ngramsFieldName);
            IndexField textField = indexLookup().get(textFieldName);

            for (String ngram : ngramsQuery) {
                IndexFieldTerm ngramsFieldTerm = ngramsField.get(ngram);
                int df = (int) ngramsFieldTerm.df();
                if (df != 0) {
                    alpha_score += Math.log(((float) ngramsField.docCount() + 2.0) /
                                            ((float) df + 1.0));
                }
            }

            for (String text : textQuery) {
                IndexFieldTerm textFieldTerm = textField.get(text);
                int df = (int) textFieldTerm.df();
                if (df != 0) {
                    beta_score += Math.log(((float) textField.docCount() + 2.0) /
                                           ((float) df + 1.0));
                }
            }

            return (alpha * alpha_score + beta * beta_score);
        } catch (IOException e) {
            throw new ScriptException("Could not compute score: ", e);
        }
    }
}
