package bfg.recorder;

import java.nio.file.Paths;
import java.util.Properties;

public class RecorderFactory {
	private static final String PROP_DIRECTORY = "run.directory";

	public static Recorder getInstance(Properties props) {
		return new Recorder(Paths.get(props.getProperty(PROP_DIRECTORY)));
	}
}
