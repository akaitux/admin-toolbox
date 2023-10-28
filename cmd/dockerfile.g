// package cmd
//
// import (
// 	"bufio"
// 	"errors"
//     "fmt"
// 	"os"
// 	"strings"
//     "github.com/docker/docker/client"
// )
// )
//
//
// type Dockerfile struct {
//     Path       string
//     Content    string
// }
//
// func NewDockerFile() Dockerfile {
//     return Dockerfile {
//         Path: Config.Workdir + "/Dockerfile",
//     }
// }
//
//
// func (dfile *Dockerfile) validateNonRoot() error {
//     if dfile.Content == "" {
//         return errors.New("Custom Dockerfile is empty")
//     }
//     scanner := bufio.NewScanner(strings.NewReader(dfile.Content))
//     banWords := []string{"USER", "COPY", "ADD", "CMD", "ENTRYPOINT"}
//     for scanner.Scan() {
//         line := scanner.Text()
//         for _, banWord := range(banWords) {
//             if strings.HasPrefix(line, banWord) {
//                 return fmt.Errorf("'%s' restrict in custom dockerfile", banWord)
//             }
//         }
//     }
//     return nil
// }
//
//
// func (dfile *Dockerfile) Save() error {
//     return os.WriteFile(dfile.Path, []byte(dfile.Content), 0600)
// }
//
//
// func (dfile *Dockerfile) Build(cli *Client) error {
//     cli.ImageBuild(context.Background(), GetContext("~/repos/myrepo"), types.ImageBuildOptions{...}
//
// }
//
// func getContext(filePath string) io.Reader {
//     ctx, _ := archive.TarWithOptions(filePath, &archive.TarOptions{})
//     return ctx
// }
//
