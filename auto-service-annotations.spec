Name:		auto-service-annotations
Version:	1.1.1
Release:	1
Summary:	AutoService provider-configuration annotation
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/google/auto/tree/main/service
Source0:	https://github.com/google/auto/archive/refs/tags/auto-service-%{version}.tar.gz#/auto-service-annotations-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar

%description
@AutoService marks a class as a java.util.ServiceLoader provider. This
package is the annotation only. AutoValue's processors are annotated
with it. The processor that writes META-INF/services files is not in
this jar.

%prep
%autosetup -n auto-auto-service-%{version} -p1
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
find service/annotations/src/main/java -name '*.java' ! -name 'module-info.java' > sources.list
test "$(wc -l < sources.list)" -eq 1
mkdir -p classes
javac --release 8 -encoding UTF-8 -d classes @sources.list
jar cf auto-service-annotations.jar -C classes .
jar tf auto-service-annotations.jar | grep -E '\.(java|jar|so|node|wasm)$' && exit 1 || true
javap -verbose -cp auto-service-annotations.jar com.google.auto.service.AutoService | grep -F 'major version: 52'

cat > auto-service-annotations.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.google.auto.service</groupId>
  <artifactId>auto-service-annotations</artifactId>
  <version>1.1.1</version>
  <name>AutoService Annotations</name>
  <description>Annotation for java.util.ServiceLoader providers</description>
  <licenses>
    <license>
      <name>Apache-2.0</name>
    </license>
  </licenses>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact auto-service-annotations.pom:auto-service-annotations.jar \
	--file-name auto-service-annotations \
	--filelist .mfiles

%check
mkdir -p check
cat > check/Smoke.java << 'END'
import com.google.auto.service.AutoService;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
public class Smoke {
	@AutoService(Runnable.class)
	public static final class Provider implements Runnable {
		public void run() {}
	}

	public static void main(String[] args) throws Exception {
		Retention retention = AutoService.class.getAnnotation(Retention.class);
		if (retention == null || retention.value() != RetentionPolicy.CLASS) {
			throw new RuntimeException("retention " + retention);
		}
		if (!AutoService.class.getMethod("value").getReturnType().equals(Class[].class)) {
			throw new RuntimeException("value method");
		}
		System.out.println("auto_service_ok " + retention.value());
	}
}
END
JAR=%{buildroot}%{_javadir}/auto-service-annotations.jar
test -f "$JAR"
javac --release 8 -encoding UTF-8 -cp "$JAR" -d check check/Smoke.java
javap -v -cp check 'Smoke$Provider' > check/javap.txt
grep -F -q 'com.google.auto.service.AutoService' check/javap.txt
java -cp "check:$JAR" Smoke > check/out.txt
cat check/out.txt
grep -F -q 'auto_service_ok CLASS' check/out.txt

%files -f .mfiles
%doc LICENSE
