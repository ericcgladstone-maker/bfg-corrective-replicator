package bfg.misc;

import java.util.ArrayList;
import java.util.List;
import java.util.Properties;

public class Utilities {
	private static Utilities instance;

	public static Utilities getInstance() {
		synchronized (Utilities.class) {
			if (instance == null)
				instance = new Utilities();
		}
		return instance;
	}

	private Utilities() {
	}

	public List<String> loadStringArray(Properties props, String arrayPreamble) {
		List<String> values = new ArrayList<>();
		String value;
		int valueNdx = 1;
		do {
			value = props.getProperty(arrayPreamble + "." + valueNdx++);
			if (value != null) {
				values.add(value);
			}
		} while (value != null);
		return values;
	}

	public List<Integer> loadIntegerArray(Properties props, String arrayPreamble) {
		List<Integer> values = new ArrayList<>();
		String value;
		int valueNdx = 1;
		do {
			value = props.getProperty(arrayPreamble + "." + valueNdx++);
			if (value != null) {
				values.add(Integer.parseInt(value, 10));
			}
		} while (value != null);
		return values;
	}

	public List<Double> loadDoubleArray(Properties props, String arrayPreamble) {
		List<Double> values = new ArrayList<>();
		String value;
		int valueNdx = 1;
		do {
			value = props.getProperty(arrayPreamble + "." + valueNdx++);
			if (value != null) {
				values.add(Double.parseDouble(value));
			}
		} while (value != null);
		return values;
	}
}
